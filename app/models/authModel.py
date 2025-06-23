from pydantic import BaseModel, EmailStr

class UserPublic(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str

    class Config:
        orm_mode = True
