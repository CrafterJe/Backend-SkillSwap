#app/routes/auth.py
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel
from app.schemas.authSchema import UserCreate
from app.utils.authUtils import create_token_pair, verify_refresh_token, create_access_token
from app.utils.securityUtils import hash_password, verify_password
from app.utils.auth_guardUtils import auth_required, get_current_user, auth_required_depends
from app.database import user_collection
from datetime import datetime, date
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["Auth"])

# Schemas
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/signup")
async def signup(user: UserCreate):
    """Registro de nuevo usuario"""
    existing = await user_collection.find_one({
        "$or": [{"username": user.username}, {"email": user.email}]
    })

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario o correo ya está registrado"
        )

    user_data = user.dict()

    # Convertir fecha si es necesario
    if isinstance(user_data["birth_date"], date):
        user_data["birth_date"] = datetime.combine(user_data["birth_date"], datetime.min.time())

    # Hashear la contraseña
    user_data["password"] = hash_password(user.password)

    # Imagen de perfil por defecto según género
    DEFAULT_IMAGES = {
        "masculino": "https://firebasestorage.googleapis.com/v0/b/skillswap-app-f701e.firebasestorage.app/o/avatars%2Fdefault-profile-male.png?alt=media&token=47aff76b-a7cc-4b81-99fa-93e9d1632d88",
        "femenino": "https://firebasestorage.googleapis.com/v0/b/skillswap-app-f701e.firebasestorage.app/o/avatars%2Fdefault-profile-female.png?alt=media&token=cd350111-5013-4572-a4b9-957e1a476839",
        "otro": "https://firebasestorage.googleapis.com/v0/b/skillswap-app-f701e.firebasestorage.app/o/avatars%2Fdefault-profile-other.png?alt=media&token=4d42b14e-c167-480a-8193-83f5d66f141b"
    }

    gender_key = user.gender.strip().lower()
    profile_image_url = DEFAULT_IMAGES.get(gender_key, DEFAULT_IMAGES["masculino"])
    user_data["profile_image"] = profile_image_url

    # Inicializar seguidores y seguidos vacíos
    user_data["followers"] = []
    user_data["following"] = []
    
    # Agregar timestamp de creación
    user_data["created_at"] = datetime.utcnow()
    user_data["last_login"] = datetime.utcnow()

    result = await user_collection.insert_one(user_data)
    user_id = str(result.inserted_id)

    # Crear ambos tokens
    tokens = create_token_pair({"sub": user_id})

    return {
        "message": "Usuario registrado exitosamente",
        **tokens,  # Incluye access_token, refresh_token, token_type, expires_in
        "user": {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "about_me": user.about_me,
            "profile_image": profile_image_url
        }
    }


@router.post("/login")
async def login(data: LoginRequest):
    """Iniciar sesión"""
    user = await user_collection.find_one({"username": data.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    if not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta"
        )

    # Actualizar último login
    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )

    # Crear ambos tokens
    tokens = create_token_pair({"sub": str(user["_id"])})

    user_data = {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "about_me": user.get("about_me", ""),
        "profile_image": str(user.get("profile_image") or ""),
        "last_login": user.get("last_login")
    }

    return {
        "message": "Login exitoso",
        **tokens,  # Incluye access_token, refresh_token, token_type, expires_in
        "user": user_data
    }


@router.post("/refresh")
async def refresh_access_token(request: RefreshTokenRequest):
    """Renovar access token usando refresh token"""
    try:
        # Verificar el refresh token
        payload = verify_refresh_token(request.refresh_token)
        
        # Extraer el user_id del payload
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload inválido"
            )
        
        # Verificar que el usuario aún existe en la base de datos
        try:
            user = await user_collection.find_one({"_id": ObjectId(user_id)})
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no válido"
            )
            
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        # Crear nuevo access token
        new_access_token = create_access_token({"sub": user_id})
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hora
            "message": "Token renovado exitosamente"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al renovar token"
        )


@router.post("/logout")
async def logout(request: RefreshTokenRequest):
    """Cerrar sesión - Invalida el refresh token"""
    try:
        # Verificar que el refresh token es válido antes de invalidarlo
        payload = verify_refresh_token(request.refresh_token)
        
        # Aquí podrías agregar el refresh token a una blacklist en tu base de datos
        # Por ahora, simplemente validamos que el token era correcto
        
        # Opcional: Crear una colección de blacklist para tokens invalidados
        # blacklist_data = {
        #     "token": request.refresh_token,
        #     "user_id": payload.get("sub"),
        #     "blacklisted_at": datetime.utcnow(),
        #     "reason": "user_logout"
        # }
        # await blacklist_collection.insert_one(blacklist_data)
        
        return {
            "message": "Sesión cerrada exitosamente",
            "logged_out": True
        }
        
    except HTTPException as e:
        # Aunque el token sea inválido, consideramos el logout exitoso
        return {
            "message": "Sesión cerrada exitosamente",
            "logged_out": True
        }
    except Exception as e:
        return {
            "message": "Sesión cerrada exitosamente",
            "logged_out": True
        }


@router.get("/verify")
async def verify_token(current_user_id: str = Depends(auth_required_depends)):
    """Verificar si un token es válido y obtener info del usuario"""
    try:
        # Obtener información actualizada del usuario
        user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        return {
            "message": "Token válido",
            "user": {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "about_me": user.get("about_me", ""),
                "profile_image": str(user.get("profile_image") or "")
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


@router.get("/me")
async def get_current_user_info(current_user_id: str = Depends(auth_required_depends)):
    """Obtener información del usuario actual"""
    try:
        user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Convertir fechas y ObjectIds a strings para serialización JSON
        def serialize_datetime(dt):
            return dt.isoformat() if dt else None
        
        def serialize_objectid_list(obj_list):
            return [str(obj_id) for obj_id in obj_list] if obj_list else []
        
        return {
            "user": {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "about_me": user.get("about_me", ""),
                "profile_image": str(user.get("profile_image") or ""),
                "followers": serialize_objectid_list(user.get("followers", [])),
                "following": serialize_objectid_list(user.get("following", [])),
                "created_at": serialize_datetime(user.get("created_at")),
                "last_login": serialize_datetime(user.get("last_login"))
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )