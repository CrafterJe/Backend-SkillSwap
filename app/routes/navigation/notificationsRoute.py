#app/routes/notificationsRoute.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.database import notification_collection, user_collection
from app.schemas.navigation.notificationsSchema import NotificationResponse, PushTokenRequest
from app.utils.auth_guardUtils import auth_required_depends
from bson import ObjectId
from datetime import datetime

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

# ========= OBTENER NOTIFICACIONES DEL USUARIO ACTUAL =========
@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(current_user_id: str = Depends(auth_required_depends)):
    notifications_cursor = notification_collection.find(
        {"to_user": ObjectId(current_user_id)},
        sort=[("created_at", -1)]
    )

    notifications = await notifications_cursor.to_list(length=50)
    enriched_notifications = []

    for notif in notifications:
        from_user = await user_collection.find_one(
            {"_id": notif["from_user"]},
            {"username": 1, "first_name": 1, "last_name": 1, "profile_image": 1}
        )

        # Evita error si el usuario ya no existe
        if not from_user:
            continue

        enriched_notifications.append({
            "id": str(notif["_id"]),
            "type": notif["type"],
            "message": notif["message"],
            "created_at": notif["created_at"].isoformat() if notif.get("created_at") else None,
            "read": notif.get("read", False),
            "from_user": {
                "id": str(from_user["_id"]),
                "username": from_user["username"],
                "first_name": from_user.get("first_name", ""),
                "last_name": from_user.get("last_name", ""),
                "profile_image": from_user.get("profile_image", "")
            }
        })

    return enriched_notifications

# ========= MARCAR NOTIFICACIÓN COMO LEÍDA =========
@router.patch("/{notification_id}/read")
async def mark_notification_as_read(notification_id: str, current_user_id: str = Depends(auth_required_depends)):
    result = await notification_collection.update_one(
        {
            "_id": ObjectId(notification_id),
            "to_user": ObjectId(current_user_id)
        },
        {"$set": {"read": True}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada o ya leída")

    return {"message": "Notificación marcada como leída"}


@router.patch("/read/all")
async def mark_all_as_read(current_user_id: str = Depends(auth_required_depends)):
    result = await notification_collection.update_many(
        {
            "to_user": ObjectId(current_user_id),
            "read": False
        },
        {"$set": {"read": True}}
    )

    return {"message": f"{result.modified_count} notificaciones marcadas como leídas"}


@router.post("/push-token")
async def update_push_token(payload: PushTokenRequest, current_user_id: str = Depends(auth_required_depends)):
    result = await user_collection.update_one(
    {"_id": ObjectId(current_user_id)},
    {"$set": {"expo_push_token": payload.token}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Ya no forzamos que modified_count sea > 0
    return {"message": "Token actualizado correctamente"}
    