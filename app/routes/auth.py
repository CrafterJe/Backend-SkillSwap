from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserCreate
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.auth_guard import auth_required
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

    if isinstance(user_data["birth_date"], date):
        user_data["birth_date"] = datetime.combine(user_data["birth_date"], datetime.min.time())

    user_data["password"] = hash_password(user.password)
    await user_collection.insert_one(user_data)

    return {"message": "Usuario registrado correctamente"}


@router.post("/login")
async def login(data: dict):
    username = data.get("username")
    password = data.get("password")

    user = await user_collection.find_one({ "username": username })
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    token = create_access_token({"sub": str(user["_id"])})
    return {"access_token": token}
