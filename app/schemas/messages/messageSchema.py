# app/schemas/messages/messageSchema.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SendMessageRequest(BaseModel):
    recipient_username: str = Field(..., min_length=3, max_length=30)
    content: str = Field(..., min_length=1, max_length=1000)

class MessageUser(BaseModel):
    id: str
    username: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    profile_image: Optional[str] = ""

class MessageResponse(BaseModel):
    id: str
    sender: MessageUser
    content: str
    created_at: datetime
    is_read: bool

class ConversationResponse(BaseModel):
    id: str
    other_user: MessageUser
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int
    updated_at: datetime

class ConversationDetailResponse(BaseModel):
    id: str
    other_user: MessageUser
    messages: List[MessageResponse]