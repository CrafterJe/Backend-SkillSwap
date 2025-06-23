# routes/navigation/profile.py
from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth_guardUtils import auth_required
from app.database import user_collection
from app.schemas.navigation.profileSchema import UserProfile
from bson import ObjectId

router = APIRouter(prefix="/navigation/profile", tags=["Navigation - Profile"])

@router.get("", response_model=UserProfile)
async def get_profile(user_id: str = Depends(auth_required)):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "username": user["username"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone": user.get("phone"),
        "birth_date": user["birth_date"].strftime("%Y-%m-%d"),
        "location": user.get("location"),
        "interests": user.get("interests"),
        "allow_be_added": user.get("allow_be_added", True),
        "about_me": user.get("about_me"),
    }
