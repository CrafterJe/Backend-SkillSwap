from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# colección de usuarios
user_collection = db["users"]
# colección de notificaciones
notification_collection = db["notifications"]