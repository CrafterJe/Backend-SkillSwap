# app/schemas/posts/exploreSchema.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SkillCategory(BaseModel):
    """Categoría de habilidad con estadísticas"""
    skill_name: str
    posts_offering: int
    posts_seeking: int
    total_posts: int
    preview_posts: List[dict] = []  # 3-4 posts de preview

class ExploreResponse(BaseModel):
    """Respuesta del endpoint explore"""
    categories: List[SkillCategory]
    total_skills: int

class SkillDetailResponse(BaseModel):
    """Respuesta de posts de una habilidad específica"""
    skill_name: str
    offering_posts: List[dict]
    seeking_posts: List[dict]
    total_posts: int
    has_more: bool = False

class SearchSkillRequest(BaseModel):
    """Request para búsqueda de habilidades"""
    query: str = Field(..., min_length=1)
    filter_type: Optional[str] = Field(None, pattern="^(offering|seeking|all)$")