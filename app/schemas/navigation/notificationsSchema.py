from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationUser(BaseModel):
    id: str
    username: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    profile_image: Optional[str] = ""

class NotificationResponse(BaseModel):
    id: str
    type: str
    message: str
    created_at: datetime
    read: bool
    from_user: NotificationUser
    
class PushTokenRequest(BaseModel):
    token: str