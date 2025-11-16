#app/routes/auth.py
from app.schemas.oauth_schemas import GoogleAuthRequest, CompleteProfileRequest
from app.utils.google_oauth_utils import verify_google_token
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
    
    # Asegurar que los arrays de habilidades estén inicializados
    user_data["interests_offered"] = user_data.get("interests_offered", [])
    user_data["interests_wanted"] = user_data.get("interests_wanted", [])
    
    # Agregar timestamp de creación
    user_data["created_at"] = datetime.utcnow()
    user_data["last_login"] = datetime.utcnow()

    result = await user_collection.insert_one(user_data)
    user_id = str(result.inserted_id)

    # Crear ambos tokens
    tokens = create_token_pair({"sub": user_id})

    return {
        "message": "Usuario registrado exitosamente",
        **tokens,
        "user": {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "about_me": user.about_me,
            "interests_offered": user.interests_offered,
            "interests_wanted": user.interests_wanted,
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
        "interests_offered": user.get("interests_offered", []),
        "interests_wanted": user.get("interests_wanted", []),
        "profile_image": str(user.get("profile_image") or ""),
        "last_login": user.get("last_login")
    }

    return {
        "message": "Login exitoso",
        **tokens,
        "user": user_data
    }


@router.post("/refresh")
async def refresh_access_token(request: RefreshTokenRequest):
    """Renovar access token usando refresh token"""
    try:
        payload = verify_refresh_token(request.refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload inválido"
            )
        
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
        
        new_access_token = create_access_token({"sub": user_id})
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 3600,
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
        payload = verify_refresh_token(request.refresh_token)
        
        return {
            "message": "Sesión cerrada exitosamente",
            "logged_out": True
        }
        
    except HTTPException as e:
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
                "interests_offered": user.get("interests_offered", []),
                "interests_wanted": user.get("interests_wanted", []),
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
                "interests_offered": user.get("interests_offered", []),
                "interests_wanted": user.get("interests_wanted", []),
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
@router.post("/google")
async def google_auth(request: GoogleAuthRequest):
    """
    Autenticación con Google OAuth
    - Si el usuario ya existe: retorna tokens + user
    - Si es nuevo: crea usuario y marca needs_profile_completion=True
    """
    # Verificar el token con Google
    google_user = await verify_google_token(request.id_token)
    
    if not google_user.get('email_verified'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email de Google no está verificado"
        )
    
    email = google_user['email']
    google_id = google_user['google_id']
    
    # Buscar si el usuario ya existe (por email o google_id)
    existing_user = await user_collection.find_one({
        "$or": [
            {"email": email},
            {"google_id": google_id}
        ]
    })
    
    if existing_user:
        # Usuario existe - LOGIN
        
        # Si el usuario fue creado con email/password, actualizar para agregar google_id
        if not existing_user.get('google_id'):
            await user_collection.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "google_id": google_id,
                        "auth_provider": "both",  # Ahora puede usar ambos métodos
                        "last_login": datetime.utcnow()
                    }
                }
            )
        else:
            # Solo actualizar último login
            await user_collection.update_one(
                {"_id": existing_user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        
        # Crear tokens
        user_id = str(existing_user["_id"])
        tokens = create_token_pair({"sub": user_id})
        
        return {
            "message": "Login exitoso con Google",
            **tokens,
            "needs_profile_completion": False,
            "user": {
                "id": user_id,
                "username": existing_user["username"],
                "email": existing_user["email"],
                "first_name": existing_user.get("first_name", ""),
                "last_name": existing_user.get("last_name", ""),
                "about_me": existing_user.get("about_me", ""),
                "interests_offered": existing_user.get("interests_offered", []),
                "interests_wanted": existing_user.get("interests_wanted", []),
                "profile_image": str(existing_user.get("profile_image") or "")
            }
        }
    
    else:
        # Usuario nuevo - REGISTRO
        
        # Generar username único basado en email
        base_username = email.split('@')[0].replace('.', '_').replace('-', '_').lower()
        username = base_username
        counter = 1
        
        while await user_collection.find_one({"username": username}):
            username = f"{base_username}{counter}"
            counter += 1
        
        # Imagen de perfil de Google o default
        profile_image = google_user.get('picture') or "https://firebasestorage.googleapis.com/v0/b/skillswap-app-f701e.firebasestorage.app/o/avatars%2Fdefault-profile-other.png?alt=media&token=4d42b14e-c167-480a-8193-83f5d66f141b"
        
        # Crear nuevo usuario
        new_user = {
            "username": username,
            "email": email,
            "google_id": google_id,
            "auth_provider": "google",
            "password": None,  # Sin contraseña para OAuth
            "first_name": google_user.get('given_name', ''),
            "last_name": google_user.get('family_name', ''),
            "profile_image": profile_image,
            "about_me": "",
            "phone": None,
            "gender": "otro",  # Default, puede cambiarlo después
            "birth_date": None,  # Opcional para OAuth
            "location": None,
            "interests_offered": [],
            "interests_wanted": [],
            "allow_be_added": True,
            "followers": [],
            "following": [],
            "needs_profile_completion": True,  # ← IMPORTANTE
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        result = await user_collection.insert_one(new_user)
        user_id = str(result.inserted_id)
        
        # Crear tokens
        tokens = create_token_pair({"sub": user_id})
        
        return {
            "message": "Usuario registrado con Google exitosamente",
            **tokens,
            "needs_profile_completion": True,  # ← Frontend debe mostrar formulario
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "first_name": new_user["first_name"],
                "last_name": new_user["last_name"],
                "about_me": "",
                "interests_offered": [],
                "interests_wanted": [],
                "profile_image": profile_image
            }
        }


@router.post("/complete-profile")
async def complete_profile(
    request: CompleteProfileRequest,
    current_user_id: str = Depends(auth_required_depends)
):
    """
    Completar perfil de usuario OAuth (agregar skills)
    Solo para usuarios que tienen needs_profile_completion=True
    """
    # Buscar usuario
    user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que necesita completar perfil
    if not user.get("needs_profile_completion", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El perfil ya está completo"
        )
    
    # Validar que las skills no excedan el límite
    if len(request.interests_offered) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 10 habilidades que puedes ofrecer"
        )
    
    # Preparar update
    update_data = {
        "interests_offered": request.interests_offered,
        "interests_wanted": request.interests_wanted,
        "needs_profile_completion": False  # ← Marcar como completo
    }
    
    # Si envió about_me, actualizarlo
    if request.about_me:
        update_data["about_me"] = request.about_me
    
    # Si envió username personalizado, verificar que no exista
    if request.username and request.username != user["username"]:
        existing = await user_collection.find_one({"username": request.username})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El username ya está en uso"
            )
        update_data["username"] = request.username
    
    # Actualizar usuario
    await user_collection.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$set": update_data}
    )
    
    # Obtener usuario actualizado
    updated_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
    
    return {
        "message": "Perfil completado exitosamente",
        "user": {
            "id": str(updated_user["_id"]),
            "username": updated_user["username"],
            "email": updated_user["email"],
            "first_name": updated_user.get("first_name", ""),
            "last_name": updated_user.get("last_name", ""),
            "about_me": updated_user.get("about_me", ""),
            "interests_offered": updated_user.get("interests_offered", []),
            "interests_wanted": updated_user.get("interests_wanted", []),
            "profile_image": str(updated_user.get("profile_image") or "")
        }
    }


