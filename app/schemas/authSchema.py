from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import date
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)  # Agregar validación mínima
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    gender: str = Field(..., pattern="^(masculino|femenino|otro)$")  # Validar valores permitidos
    birth_date: date
    location: Optional[str] = Field(None, max_length=100)
    interests: Optional[str] = Field(None, max_length=500)
    allow_be_added: Optional[bool] = True
    about_me: Optional[str] = Field(None, max_length=500)

    @model_validator(mode='after')
    def validate_birth_date(self):
        from datetime import date, timedelta
        min_age = date.today() - timedelta(days=365 * 13)  # Mínimo 13 años
        max_age = date.today() - timedelta(days=365 * 120)  # Máximo 120 años
        
        if self.birth_date > min_age:
            raise ValueError('Debes tener al menos 13 años')
        if self.birth_date < max_age:
            raise ValueError('Fecha de nacimiento no válida')
        
        return self

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)

class UserResponse(BaseModel):
    """Schema para respuestas de usuario (sin password)"""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    gender: str
    birth_date: Optional[str] = None  # Como string ISO format
    location: Optional[str] = None
    interests: Optional[str] = None
    allow_be_added: bool = True
    about_me: Optional[str] = None
    profile_image: str
    followers: list[str] = []
    following: list[str] = []
    created_at: Optional[str] = None
    last_login: Optional[str] = None

class TokenResponse(BaseModel):
    """Schema para respuestas de autenticación"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserResponse

class RefreshResponse(BaseModel):
    """Schema para respuesta de refresh token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    message: str = "Token renovado exitosamente"