from pydantic import BaseModel, EmailStr
from typing import Optional

class UserProfile(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str]
    birth_date: str
    location: Optional[str]
    interests: Optional[str]
    allow_be_added: Optional[bool]
    about_me: Optional[str]
