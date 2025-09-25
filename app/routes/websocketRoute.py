# app/routes/websocketRoute.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.utils.websocket_manager import manager
from app.utils.authUtils import verify_access_token
from app.database import user_collection
from bson import ObjectId
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint para mensajes en tiempo real"""
    
    # Verificar token de autenticación
    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Token inválido")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Token inválido")
        return
    
    # Verificar que el usuario existe
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        await websocket.close(code=4001, reason="Usuario no encontrado")
        return
    
    # Conectar usuario
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Escuchar mensajes del cliente
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Responder a ping para mantener conexión viva
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
                elif message_type == "typing":
                    # Notificar que el usuario está escribiendo
                    recipient_username = message.get("recipient_username")
                    if recipient_username:
                        recipient = await user_collection.find_one({"username": recipient_username})
                        if recipient:
                            typing_message = {
                                "type": "user_typing",
                                "data": {
                                    "sender_username": user["username"],
                                    "is_typing": message.get("is_typing", True)
                                }
                            }
                            await manager.send_personal_message(typing_message, str(recipient["_id"]))
                
            except json.JSONDecodeError:
                # Ignorar mensajes que no sean JSON válidos
                pass
                
    except WebSocketDisconnect:
        # Desconectar usuario
        manager.disconnect(websocket, user_id)