# app/routes/messageRoute.py
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.messages.messageSchema import SendMessageRequest, MessageResponse, ConversationResponse, ConversationDetailResponse, MessageUser
from app.utils.auth_guardUtils import auth_required_depends
from app.models.messageModel import conversation_collection, message_collection
from app.database import user_collection, notification_collection
from app.utils.websocket_manager import manager
from app.utils.push_notifications import send_push_notification
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user_id: str = Depends(auth_required_depends)):
    """Obtiene todas las conversaciones del usuario"""
    try:
        conversations = await conversation_collection.find({
            "participants": ObjectId(current_user_id)
        }).sort("updated_at", -1).to_list(length=50)
        
        result = []
        for conv in conversations:
            # Encontrar el otro usuario
            other_user_id = None
            for p in conv["participants"]:
                if str(p) != current_user_id:
                    other_user_id = p
                    break
            
            if not other_user_id:
                continue
                
            # Obtener info del otro usuario
            other_user = await user_collection.find_one({"_id": other_user_id})
            if not other_user:
                continue
            
            # Último mensaje
            last_msg = await message_collection.find_one(
                {"conversation_id": conv["_id"]},
                sort=[("created_at", -1)]
            )
            
            # Mensajes no leídos
            unread_count = await message_collection.count_documents({
                "conversation_id": conv["_id"],
                "sender_id": {"$ne": ObjectId(current_user_id)},
                "is_read": False
            })
            
            result.append(ConversationResponse(
                id=str(conv["_id"]),
                other_user=MessageUser(
                    id=str(other_user["_id"]),
                    username=other_user["username"],
                    first_name=other_user.get("first_name", ""),
                    last_name=other_user.get("last_name", ""),
                    profile_image=other_user.get("profile_image", "")
                ),
                last_message=last_msg["content"] if last_msg else None,
                last_message_at=last_msg["created_at"] if last_msg else None,
                unread_count=unread_count,
                updated_at=conv["updated_at"]
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/conversation/{username}", response_model=ConversationDetailResponse)
async def get_conversation_with_user(username: str, current_user_id: str = Depends(auth_required_depends)):
    """Obtiene mensajes con un usuario específico"""
    try:
        # Buscar el otro usuario
        other_user = await user_collection.find_one({"username": username})
        if not other_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Buscar conversación
        conversation = await conversation_collection.find_one({
            "participants": {"$all": [ObjectId(current_user_id), other_user["_id"]]}
        })
        
        messages = []
        conversation_id = ""
        
        if conversation:
            conversation_id = str(conversation["_id"])
            # Obtener mensajes
            message_docs = await message_collection.find({
                "conversation_id": conversation["_id"]
            }).sort("created_at", 1).to_list(length=1000)
            
            # Marcar como leídos los mensajes del otro usuario
            await message_collection.update_many(
                {
                    "conversation_id": conversation["_id"],
                    "sender_id": {"$ne": ObjectId(current_user_id)},
                    "is_read": False
                },
                {"$set": {"is_read": True}}
            )
            
            # Formatear mensajes
            for msg in message_docs:
                sender = await user_collection.find_one({"_id": msg["sender_id"]})
                if sender:
                    messages.append(MessageResponse(
                        id=str(msg["_id"]),
                        sender=MessageUser(
                            id=str(sender["_id"]),
                            username=sender["username"],
                            first_name=sender.get("first_name", ""),
                            last_name=sender.get("last_name", ""),
                            profile_image=sender.get("profile_image", "")
                        ),
                        content=msg["content"],
                        created_at=msg["created_at"],
                        is_read=True  # Ya los marcamos como leídos
                    ))
        
        return ConversationDetailResponse(
            id=conversation_id,
            other_user=MessageUser(
                id=str(other_user["_id"]),
                username=other_user["username"],
                first_name=other_user.get("first_name", ""),
                last_name=other_user.get("last_name", ""),
                profile_image=other_user.get("profile_image", "")
            ),
            messages=messages
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/send")
async def send_message(message_data: SendMessageRequest, current_user_id: str = Depends(auth_required_depends)):
    """Envía un mensaje"""
    try:
        # Buscar destinatario
        recipient = await user_collection.find_one({"username": message_data.recipient_username})
        if not recipient:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # La lógica del botón se mantiene en el frontend para UX
        current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
        
        # Buscar o crear conversación
        conversation = await conversation_collection.find_one({
            "participants": {"$all": [ObjectId(current_user_id), recipient["_id"]]}
        })
        
        if not conversation:
            # Crear nueva conversación
            conv_data = {
                "participants": [ObjectId(current_user_id), recipient["_id"]],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            conv_result = await conversation_collection.insert_one(conv_data)
            conversation = {"_id": conv_result.inserted_id}
        
        # Crear mensaje
        message_doc = {
            "conversation_id": conversation["_id"],
            "sender_id": ObjectId(current_user_id),
            "content": message_data.content,
            "created_at": datetime.utcnow(),
            "is_read": False
        }
        
        message_result = await message_collection.insert_one(message_doc)
        
        # Actualizar conversación
        await conversation_collection.update_one(
            {"_id": conversation["_id"]},
            {"$set": {"updated_at": datetime.utcnow()}}
        )
        
        # NUEVO: Crear objeto de respuesta con datos del mensaje
        message_response = MessageResponse(
            id=str(message_result.inserted_id),
            sender=MessageUser(
                id=str(current_user["_id"]),
                username=current_user["username"],
                first_name=current_user.get("first_name", ""),
                last_name=current_user.get("last_name", ""),
                profile_image=current_user.get("profile_image", "")
            ),
            content=message_data.content,
            created_at=message_doc["created_at"],
            is_read=False
        )
        
        # Enviar via WebSocket
        websocket_message = {
            "type": "new_message",
            "data": {
                "sender_username": current_user["username"],
                "content": message_data.content,
                "created_at": message_doc["created_at"].isoformat()
            }
        }
        
        await manager.send_personal_message(websocket_message, str(recipient["_id"]))
        
        # Enviar push notification si el usuario no está online
        if not manager.is_user_online(str(recipient["_id"])):
            # Buscar el push token del usuario (campo correcto: expo_push_token)
            if recipient.get("expo_push_token"):
                await send_push_notification(
                    token=recipient["expo_push_token"],
                    title=f"Nuevo mensaje de {current_user['username']}",
                    body=message_data.content,
                    data={
                        "type": "message",
                        "sender_username": current_user["username"],
                        "conversation_id": str(conversation["_id"])
                    }
                )
        
        # CAMBIO PRINCIPAL: Regresar datos del mensaje creado
        return {
            "message": "Mensaje enviado exitosamente",
            "data": message_response
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")