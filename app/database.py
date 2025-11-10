from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# colección de usuarios
user_collection = db["users"]

# colección de notificaciones
notification_collection = db["notifications"]

# colección de mensajes
conversation_collection = db["conversations"]
message_collection = db["messages"]

# Colecciones de posts
post_collection = db["posts"]
comment_collection = db["comments"]

# Colección de historial de búsqueda
search_history_collection = db["search_history"]
