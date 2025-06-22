from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserCreate
from app.utils.auth import hash_password
from app.database import user_collection
from datetime import datetime,date

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

    hashed_pw = hash_password(user.password)
    user_data = user.dict()

    # 🔥 Convertir birth_date (date) a datetime con hora cero
    if isinstance(user_data["birth_date"], date):
        user_data["birth_date"] = datetime.combine(user_data["birth_date"], datetime.min.time())

    user_data["password"] = hashed_pw
    await user_collection.insert_one(user_data)

    return {"message": "Usuario registrado correctamente"}