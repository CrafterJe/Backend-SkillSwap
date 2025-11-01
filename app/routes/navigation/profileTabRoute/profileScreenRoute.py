#app/routes/navigation/profileTabRoute/profileScreenRoute.py
from fastapi import APIRouter, Depends, HTTPException, Path
from app.database import user_collection, notification_collection
from app.schemas.navigation.profileTabSchema.profileScreenSchema import PublicUserProfile, FollowActionResponse
from app.utils.auth_guardUtils import auth_required_depends
from app.utils.push_notifications import send_push_notification 
from bson import ObjectId
from datetime import datetime
from typing import Optional

router = APIRouter(
    prefix="/navigation/profileTab/profileScreen",
    tags=["Navigation - Profile"]
)

@router.get("/{username}", response_model=PublicUserProfile)
async def get_public_profile(
    username: str = Path(..., min_length=3, max_length=30),
    current_user_id: Optional[str] = Depends(auth_required_depends)
):
    filtro = {"username": {"$regex": f"^{username}$", "$options": "i"}}
    user = await user_collection.find_one(filtro)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user_id = str(user["_id"])
    is_own_profile = current_user_id == user_id

    is_following = False
    if not is_own_profile and current_user_id:
        current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
        if current_user and "following" in current_user:
            is_following = ObjectId(user["_id"]) in current_user.get("following", [])

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
async def follow_user(username: str, current_user_id: str = Depends(auth_required_depends)):
    target = await user_collection.find_one({
        "username": {"$regex": f"^{username}$", "$options": "i"}
    })

    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if str(target["_id"]) == current_user_id:
        raise HTTPException(status_code=400, detail="No puedes seguirte a ti mismo")

    current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
    if current_user and target["_id"] in current_user.get("following", []):
        raise HTTPException(status_code=400, detail="Ya sigues a este usuario")

    await user_collection.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$addToSet": {"following": target["_id"]}}
    )
    await user_collection.update_one(
        {"_id": target["_id"]},
        {"$addToSet": {"followers": ObjectId(current_user_id)}}
    )

    now = datetime.utcnow()
    # Crear notificación en base de datos
    await notification_collection.insert_one({
        "to_user": target["_id"],
        "from_user": ObjectId(current_user_id),
        "type": "follow",
        "message": f"{current_user['username']} empezó a seguirte",
        "created_at": now,
        "read": False
    })

    # Enviar notificación push si tiene token
    if "expo_push_token" in target and target["expo_push_token"]:
        await send_push_notification(
            token=target["expo_push_token"],
            title="¡Nuevo seguidor!",
            body=f"{current_user['username']} empezó a seguirte",
            data={
                "type": "follow",
                "from_user": str(current_user["_id"])
            }
        )

    return {"message": f"Ahora sigues a {target['username']}"}

@router.post("/{username}/unfollow", response_model=FollowActionResponse)
async def unfollow_user(username: str, current_user_id: str = Depends(auth_required_depends)):
    target = await user_collection.find_one({
        "username": {"$regex": f"^{username}$", "$options": "i"}
    })

    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if str(target["_id"]) == current_user_id:
        raise HTTPException(status_code=400, detail="No puedes dejar de seguirte a ti mismo")

    await user_collection.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$pull": {"following": target["_id"]}}
    )
    await user_collection.update_one(
        {"_id": target["_id"]},
        {"$pull": {"followers": ObjectId(current_user_id)}}
    )

    # 🗑️ Eliminar notificación de seguimiento (si existe)
    await notification_collection.delete_many({
        "to_user": target["_id"],
        "from_user": ObjectId(current_user_id),
        "type": "follow"
    })

    return {"message": f"Has dejado de seguir a {target['username']}"}

@router.get("/{username}/followers")
async def get_user_followers(
    username: str = Path(..., min_length=3, max_length=30),
    current_user_id: str = Depends(auth_required_depends)
):
    """Obtiene la lista de seguidores de un usuario"""
    user = await user_collection.find_one({
        "username": {"$regex": f"^{username}$", "$options": "i"}
    })
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    is_own_profile = str(user["_id"]) == current_user_id
    followers_ids = user.get("followers", [])
    followers = []
    
    # Obtener info del usuario actual una sola vez
    current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
    
    for follower_id in followers_ids:
        follower = await user_collection.find_one({"_id": follower_id})
        if follower:
            # Lógica corregida para mostrar botones
            if is_own_profile:
                # En mi perfil: mostrar si YO sigo a este seguidor
                is_following = follower["_id"] in current_user.get("following", [])
                show_follow_button = True
            else:
                # En perfil ajeno: no mostrar botones de seguir
                is_following = False
                show_follow_button = False
            
            followers.append({
                "id": str(follower["_id"]),
                "username": follower["username"],
                "first_name": follower["first_name"],
                "last_name": follower["last_name"],
                "profile_image": follower.get("profile_image"),
                "is_following": is_following,
                "show_follow_button": show_follow_button
            })
    
    return {"followers": followers, "count": len(followers)}

@router.get("/{username}/following")
async def get_user_following(
    username: str = Path(..., min_length=3, max_length=30),
    current_user_id: str = Depends(auth_required_depends)
):
    """Obtiene la lista de usuarios que sigue"""
    user = await user_collection.find_one({
        "username": {"$regex": f"^{username}$", "$options": "i"}
    })
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    is_own_profile = str(user["_id"]) == current_user_id
    following_ids = user.get("following", [])
    following = []
    
    for following_id in following_ids:
        followed_user = await user_collection.find_one({"_id": following_id})
        if followed_user:
            # Lógica corregida para mostrar botones
            if is_own_profile:
                # En mi perfil → lista "siguiendo": siempre botón "Dejar de seguir"
                is_following = True
                show_follow_button = True
            else:
                # En perfil ajeno: no mostrar botones de seguir
                is_following = False
                show_follow_button = False
            
            following.append({
                "id": str(followed_user["_id"]),
                "username": followed_user["username"],
                "first_name": followed_user["first_name"],
                "last_name": followed_user["last_name"],
                "profile_image": followed_user.get("profile_image"),
                "is_following": is_following,
                "show_follow_button": show_follow_button
            })
    
    return {"following": following, "count": len(following)}