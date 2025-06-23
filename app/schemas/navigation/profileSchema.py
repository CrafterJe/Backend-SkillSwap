from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

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

class UpdateUserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    location: Optional[str] = None
    interests: Optional[str] = None
    allow_be_added: Optional[bool] = None
    about_me: Optional[str] = None
