# app/routes/messageRoute.py - CORREGIDO
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.schemas.messages.messageSchema import SendMessageRequest, MessageResponse, ConversationResponse, ConversationDetailResponse, MessageUser
from app.utils.auth_guardUtils import auth_required_depends
from app.models.messageModel import conversation_collection, message_collection
from app.database import user_collection, notification_collection
from app.utils.websocket_manager import manager
from app.utils.push_notifications import send_push_notification
from bson import ObjectId
from datetime import datetime
from typing import List
import logging

# Configurar logging
logger = logging.getLogger(__name__)

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
async def get_conversation_with_user(
    username: str, 
    current_user_id: str = Depends(auth_required_depends),
    limit: int = Query(50, ge=10, le=100, description="Número de mensajes a cargar"),
    before_id: str = Query(None, description="ID del mensaje para paginación")
):
    """Obtiene mensajes con un usuario específico (OPTIMIZADO)"""
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
            
            # Query optimizado con paginación
            query = {"conversation_id": conversation["_id"]}
            if before_id:
                # Si hay before_id, traer mensajes anteriores a ese ID
                try:
                    query["_id"] = {"$lt": ObjectId(before_id)}
                except:
                    pass
            
            # Obtener mensajes (limitado)
            message_docs = await message_collection.find(query)\
                .sort("created_at", -1)\
                .limit(limit)\
                .to_list(length=limit)
            
            # Invertir para tener orden cronológico
            message_docs.reverse()
            
            # Marcar como leídos los mensajes del otro usuario
            await message_collection.update_many(
                {
                    "conversation_id": conversation["_id"],
                    "sender_id": {"$ne": ObjectId(current_user_id)},
                    "is_read": False
                },
                {"$set": {"is_read": True}}
            )
            
            # OPTIMIZACIÓN: Obtener TODOS los senders únicos en una sola query
            sender_ids = list(set(msg["sender_id"] for msg in message_docs))
            senders = await user_collection.find(
                {"_id": {"$in": sender_ids}}
            ).to_list(length=len(sender_ids))
            
            # Crear mapa de senders para acceso rápido
            sender_map = {
                str(sender["_id"]): MessageUser(
                    id=str(sender["_id"]),
                    username=sender["username"],
                    first_name=sender.get("first_name", ""),
                    last_name=sender.get("last_name", ""),
                    profile_image=sender.get("profile_image", "")
                )
                for sender in senders
            }
            
            # Formatear mensajes usando el mapa (sin queries adicionales)
            for msg in message_docs:
                sender_id = str(msg["sender_id"])
                sender = sender_map.get(sender_id)
                
                if sender:
                    messages.append(MessageResponse(
                        id=str(msg["_id"]),
                        sender=sender,
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
        # 🔍 LOG: Inicio del envío
        logger.info(f"📨 Enviando mensaje de {current_user_id} a {message_data.recipient_username}")
        
        # Buscar destinatario
        recipient = await user_collection.find_one({"username": message_data.recipient_username})
        if not recipient:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        recipient_id = str(recipient["_id"])
        logger.info(f"✅ Destinatario encontrado: {recipient_id}")
        
        # Obtener usuario actual
        current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
        
        # Buscar o crear conversación
        conversation = await conversation_collection.find_one({
            "participants": {"$all": [ObjectId(current_user_id), recipient["_id"]]}
        })
        
        is_new_conversation = conversation is None
        
        if not conversation:
            # Crear nueva conversación
            logger.info(f"🆕 Creando nueva conversación")
            conv_data = {
                "participants": [ObjectId(current_user_id), recipient["_id"]],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            conv_result = await conversation_collection.insert_one(conv_data)
            conversation = {"_id": conv_result.inserted_id}
        else:
            logger.info(f"✅ Conversación existente: {str(conversation['_id'])}")
        
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
        
        # Crear objeto de respuesta
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
        
        # 🔔 ENVIAR VIA WEBSOCKET AL DESTINATARIO
        websocket_message = {
            "type": "new_message",
            "data": {
                "sender_username": current_user["username"],
                "content": message_data.content,
                "created_at": message_doc["created_at"].isoformat(),
                "is_new_conversation": is_new_conversation  # 🆕 AÑADIDO
            }
        }
        
        # Verificar si el destinatario está conectado
        is_recipient_online = manager.is_user_online(recipient_id)
        logger.info(f"🔌 Destinatario online: {is_recipient_online}")
        
        if is_recipient_online:
            logger.info(f"📤 Enviando WebSocket a destinatario: {recipient_id}")
            await manager.send_personal_message(websocket_message, recipient_id)
            logger.info(f"✅ WebSocket enviado exitosamente")
        else:
            logger.info(f"⚠️ Destinatario offline, no se envía WebSocket")
        
        # 📲 Enviar push notification si el usuario no está online
        if not is_recipient_online:
            if recipient.get("expo_push_token"):
                logger.info(f"📲 Enviando push notification")
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
        
        logger.info(f"✅ Mensaje enviado completamente")
        
        # Retornar datos del mensaje creado
        return {
            "message": "Mensaje enviado exitosamente",
            "data": message_response
        }
        
    except HTTPException as e:
        logger.error(f"❌ HTTPException: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")