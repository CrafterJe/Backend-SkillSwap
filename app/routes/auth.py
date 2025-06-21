from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user import UserCreate  # ← asegúrate que apunta al schema correcto
from app.utils.auth import hash_password
from app.database import get_db
from pymongo.database import Database

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
def signup(user: UserCreate, db: Database = Depends(get_db)):
    existing = db.users.find_one({"$or": [{"username": user.username}, {"email": user.email}]})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario o correo ya está registrado"
        )

    hashed_pw = hash_password(user.password)
    user_data = user.dict()
    user_data["password"] = hashed_pw
    db.users.insert_one(user_data)
    return {"message": "Usuario registrado correctamente"}
