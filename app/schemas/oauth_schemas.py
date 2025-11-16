from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class GoogleAuthRequest(BaseModel):
    """Request para autenticación con Google"""
    id_token: str = Field(..., description="Token ID de Google OAuth")

class CompleteProfileRequest(BaseModel):
    """Request para completar perfil de usuario OAuth"""
    interests_offered: list[str] = Field(..., min_items=1, max_items=10, description="Habilidades que ofrece")
    interests_wanted: list[str] = Field(..., min_items=1, description="Habilidades que quiere aprender")
    username: Optional[str] = Field(None, min_length=3, max_length=30, description="Username personalizado (opcional)")
    about_me: Optional[str] = Field(None, max_length=500, description="Descripción personal")

    class Config:
        json_schema_extra = {
            "example": {
                "interests_offered": ["Programación", "Diseño Gráfico"],
                "interests_wanted": ["Inglés", "Guitarra"],
                "username": "juanperez",
                "about_me": "Desarrollador apasionado por aprender"
            }
        }