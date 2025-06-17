from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate
from app.models.user import User
from app.utils.auth import hash_password
from app.database import user_collection
from pymongo.errors import DuplicateKeyError

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register(user: UserCreate):
    existing = await user_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)

    new_user = {
        "name": user.name,
        "email": user.email,
        "password": hashed
    }

    result = await user_collection.insert_one(new_user)
    return {"id": str(result.inserted_id), "message": "User registered successfully"}
