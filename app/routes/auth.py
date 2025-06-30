from fastapi import APIRouter, HTTPException, status
from app.schemas.authSchema import UserCreate
from app.utils.authUtils import create_access_token
from app.utils.securityUtils import hash_password, verify_password
from app.utils.auth_guardUtils import auth_required
from app.database import user_collection
from datetime import datetime, date

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
async def signup(user: UserCreate):
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

    result = await user_collection.insert_one(user_data)
    user_id = str(result.inserted_id)

    token = create_access_token({"sub": user_id})

    return {
        "access_token": token,
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
async def login(data: dict):
    username = data.get("username")
    password = data.get("password")

    user = await user_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    token = create_access_token({"sub": str(user["_id"])})

    user_data = {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "about_me": user.get("about_me", ""),
        "profile_image": str(user.get("profile_image") or "")
        # "followers": user.get("followers", []),       ← opcional en el futuro
        # "following": user.get("following", [])
    }

    return {"access_token": token, "user": user_data}
