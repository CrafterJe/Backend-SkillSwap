from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Schema para habilidades en el post
class PostSkills(BaseModel):
    offering: List[str] = []
    seeking: List[str] = []

# Schema para crear un post
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    images: List[str] = Field(default_factory=list, max_items=10)
    type: str = Field(..., pattern="^(general|skill_offer|skill_request)$")
    skills: Optional[PostSkills] = None

# Schema para actualizar un post
class PostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    images: Optional[List[str]] = Field(None, max_items=10)
    type: Optional[str] = Field(None, pattern="^(general|skill_offer|skill_request)$")
    skills: Optional[PostSkills] = None

# Schema del usuario en la respuesta
class PostUser(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    profile_image: Optional[str] = None

# Schema de respuesta de un post
class PostResponse(BaseModel):
    id: str
    user: PostUser
    content: str
    images: List[str] = []
    type: str
    skills: Optional[PostSkills] = None
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    created_at: datetime
    updated_at: datetime

# Schema para respuesta de like
class LikeResponse(BaseModel):
    message: str
    is_liked: bool
    likes_count: int

# Schema para crear comentario
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

# Schema de respuesta de comentario
class CommentResponse(BaseModel):
    id: str
    user: PostUser
    content: str
    created_at: datetime

# Schema para respuesta de lista de comentarios
class CommentsListResponse(BaseModel):
    comments: List[CommentResponse]
    count: int
    has_more: bool = False