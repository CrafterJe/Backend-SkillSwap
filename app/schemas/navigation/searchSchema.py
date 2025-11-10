# schemas/navigation/searchSchema.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class SearchUserResult(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    profile_image: Optional[str] = None

# ========== SCHEMAS DE HISTORIAL ==========

class SearchHistoryCreate(BaseModel):
    """Para guardar búsquedas de texto (queries)"""
    query: str

class UserHistoryCreate(BaseModel):
    """Para guardar usuarios clickeados"""
    user_id: str

class SearchHistoryResponse(BaseModel):
    id: str
    user_id: str
    type: Literal["query", "user"]
    query: Optional[str] = None
    clicked_user: Optional[SearchUserResult] = None
    searched_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }