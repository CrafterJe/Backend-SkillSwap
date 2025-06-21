from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    gender: str
    birth_date: date
    location: Optional[str] = None
    interests: Optional[str] = None
