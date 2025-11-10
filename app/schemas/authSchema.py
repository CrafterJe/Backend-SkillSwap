# //app/schemas/authSchema.py
from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import date
from typing import Optional

# 50 Habilidades predefinidas para la app
PREDEFINED_SKILLS = [
    "Programación", "Diseño Gráfico", "Marketing Digital", "Cocina", "Guitarra",
    "Inglés", "Francés", "Alemán", "Italiano", "Portugués",
    "Fotografía", "Yoga", "Matemáticas", "Contabilidad", "Escritura",
    "Dibujo", "Piano", "Canto", "Baile", "Teatro",
    "Edición de Video", "Illustrator", "Photoshop", "Excel", "PowerPoint",
    "Mecánica", "Electricidad", "Plomería", "Carpintería", "Jardinería",
    "Repostería", "Panadería", "Costura", "Tejido", "Bordado",
    "Maquillaje", "Peluquería", "Masajes", "Meditación", "Pilates",
    "Violín", "Batería", "Bajo", "Saxofón", "Pintura",
    "Escultura", "Cerámica", "Origami", "Caligrafía", "Otro"
]

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    gender: str = Field(..., pattern="^(masculino|femenino|otro)$")
    birth_date: date
    location: Optional[str] = Field(None, max_length=100)
    interests_offered: list[str] = Field(default_factory=list, max_items=10)
    interests_wanted: list[str] = Field(default_factory=list)
    allow_be_added: Optional[bool] = True
    about_me: Optional[str] = Field(None, max_length=500)

    @model_validator(mode='after')
    def validate_birth_date(self):
        from datetime import date, timedelta
        min_age = date.today() - timedelta(days=365 * 13)
        max_age = date.today() - timedelta(days=365 * 120)
        
        if self.birth_date > min_age:
            raise ValueError('Debes tener al menos 13 años')
        if self.birth_date < max_age:
            raise ValueError('Fecha de nacimiento no válida')
        
        return self

    @model_validator(mode='after')
    def validate_interests(self):
        if len(self.interests_offered) > 10:
            raise ValueError('Máximo 10 habilidades que puedes ofrecer')
        
        for skill in self.interests_offered + self.interests_wanted:
            if len(skill.strip()) < 2:
                raise ValueError('Cada habilidad debe tener al menos 2 caracteres')
        
        return self

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    gender: str
    birth_date: Optional[str] = None
    location: Optional[str] = None
    interests_offered: list[str] = []
    interests_wanted: list[str] = []
    allow_be_added: bool = True
    about_me: Optional[str] = None
    profile_image: str
    followers: list[str] = []
    following: list[str] = []
    created_at: Optional[str] = None
    last_login: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserResponse

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    message: str = "Token renovado exitosamente"