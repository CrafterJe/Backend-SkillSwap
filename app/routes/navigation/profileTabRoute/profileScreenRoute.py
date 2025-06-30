from fastapi import APIRouter, Depends, HTTPException, Path
from app.database import user_collection
from app.schemas.navigation.profileTabSchema.profileScreenSchema import PublicUserProfile, FollowActionResponse
from app.utils.auth_guardUtils import auth_required
from bson import ObjectId
from typing import Optional

router = APIRouter(
    prefix="/navigation/profileTab/profileScreen",
    tags=["Navigation - Profile"]
)

@router.get("/{username}", response_model=PublicUserProfile)
async def get_public_profile(
    username: str = Path(..., min_length=3, max_length=30),
    current_user_id: Optional[str] = Depends(auth_required)
):
    filtro = {
        "username": {"$regex": f"^{username}$", "$options": "i"}
    }

    user = await user_collection.find_one(filtro)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user_id = str(user["_id"])
    
    # Verificar si es el propio perfil
    is_own_profile = current_user_id == user_id
    
    # Verificar si ya sigue al usuario (solo si no es su propio perfil)
    is_following = False
    if not is_own_profile and current_user_id:
        current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
        if current_user and "following" in current_user:
            is_following = user_id in current_user.get("following", [])
    
    # Contar seguidores y seguidos
    followers_count = len(user.get("followers", []))
    following_count = len(user.get("following", []))

    return {
        "id": user_id,
        "username": user["username"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "about_me": user.get("about_me"),
        "profile_image": user.get("profile_image"),
        "is_own_profile": is_own_profile,
        "is_following": is_following,
        "followers_count": followers_count,
        "following_count": following_count
    }


@router.post("/{username}/follow", response_model=FollowActionResponse)
async def follow_user(username: str, current_user_id: str = Depends(auth_required)):
    target = await user_collection.find_one({
        "username": {"$regex": f"^{username}$", "$options": "i"}
    })

    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if str(target["_id"]) == current_user_id:
        raise HTTPException(status_code=400, detail="No puedes seguirte a ti mismo")

    # Verificar si ya sigue al usuario
    current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
    if current_user and str(target["_id"]) in current_user.get("following", []):
        raise HTTPException(status_code=400, detail="Ya sigues a este usuario")

    await user_collection.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$addToSet": {"following": str(target["_id"])}}
    )
    await user_collection.update_one(
        {"_id": target["_id"]},
        {"$addToSet": {"followers": current_user_id}}
    )

    return {"message": f"Ahora sigues a {target['username']}"}


@router.post("/{username}/unfollow", response_model=FollowActionResponse)
async def unfollow_user(username: str, current_user_id: str = Depends(auth_required)):
    target = await user_collection.find_one({
        "username": {"$regex": f"^{username}$", "$options": "i"}
    })

    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if str(target["_id"]) == current_user_id:
        raise HTTPException(status_code=400, detail="No puedes dejar de seguirte a ti mismo")

    await user_collection.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$pull": {"following": str(target["_id"])}}
    )
    await user_collection.update_one(
        {"_id": target["_id"]},
        {"$pull": {"followers": current_user_id}}
    )

    return {"message": f"Has dejado de seguir a {target['username']}"}