# app/models/messageModel.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Nuevas colecciones para mensajes
conversation_collection = db["conversations"]
message_collection = db["messages"]