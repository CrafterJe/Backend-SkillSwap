# app/routes/explore/exploreRoute.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.schemas.explore.exploreSchema import (
    ExploreResponse, 
    SkillCategory, 
    SkillDetailResponse,
    SearchSkillRequest
)
from app.utils.auth_guardUtils import auth_required_depends
from app.database import post_collection, user_collection
from app.schemas.authSchema import PREDEFINED_SKILLS
from bson import ObjectId
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/explore", tags=["Explore"])


async def format_post_simple(post: dict, current_user_id: str) -> dict:
    """Formato simplificado de post para explore"""
    user = await user_collection.find_one({"_id": post["user_id"]})
    
    if not user:
        return None
    
    is_liked = ObjectId(current_user_id) in post.get("likes", [])
    
    return {
        "id": str(post["_id"]),
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "profile_image": user.get("profile_image")
        },
        "content": post["content"][:100] + "..." if len(post["content"]) > 100 else post["content"],
        "images": post.get("images", [])[:1],
        "type": post["type"],
        "skills": post.get("skills"),
        "likes_count": post.get("likes_count", 0),
        "comments_count": post.get("comments_count", 0),
        "is_liked": is_liked,
        "created_at": post["created_at"]
    }


@router.get("/categories", response_model=ExploreResponse)
async def get_explore_categories(
    current_user_id: str = Depends(auth_required_depends),
    limit: int = Query(20, ge=5, le=50, description="Número de categorías")
):
    """
    Obtener categorías de habilidades con estadísticas usando aggregation (OPTIMIZADO)
    """
    try:
        import time
        start_time = time.time()
        
        # ⚡ AGGREGATION PIPELINE - 1 SOLA QUERY para todo
        pipeline = [
            # Filtrar solo posts con skills
            {
                "$match": {
                    "type": {"$in": ["skill_offer", "skill_request"]},
                    "skills": {"$ne": None}
                }
            },
            # Descomponer arrays de skills
            {
                "$project": {
                    "type": 1,
                    "user_id": 1,
                    "content": 1,
                    "images": 1,
                    "skills": 1,
                    "likes": 1,
                    "likes_count": 1,
                    "comments_count": 1,
                    "created_at": 1,
                    "all_skills": {
                        "$concatArrays": [
                            {"$ifNull": ["$skills.offering", []]},
                            {"$ifNull": ["$skills.seeking", []]}
                        ]
                    }
                }
            },
            # Desenrollar el array de skills
            {"$unwind": "$all_skills"},
            # Agrupar por skill y contar
            {
                "$group": {
                    "_id": "$all_skills",
                    "posts_offering": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$type", "skill_offer"]},
                                        {"$in": ["$all_skills", {"$ifNull": ["$skills.offering", []]}]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    },
                    "posts_seeking": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$type", "skill_request"]},
                                        {"$in": ["$all_skills", {"$ifNull": ["$skills.seeking", []]}]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    },
                    "preview_posts": {"$push": "$$ROOT"}
                }
            },
            # Calcular total y limitar previews
            {
                "$project": {
                    "skill_name": "$_id",
                    "posts_offering": 1,
                    "posts_seeking": 1,
                    "total_posts": {"$add": ["$posts_offering", "$posts_seeking"]},
                    "preview_posts": {"$slice": ["$preview_posts", 3]}
                }
            },
            # Ordenar por total de posts
            {"$sort": {"total_posts": -1}},
            # Limitar resultados
            {"$limit": limit}
        ]
        
        results = await post_collection.aggregate(pipeline).to_list(length=limit)
        
        # Formatear resultados
        categories_data = []
        
        # Obtener todos los user_ids únicos de los previews
        all_user_ids = set()
        for result in results:
            for post in result.get("preview_posts", []):
                all_user_ids.add(post["user_id"])
        
        # Cargar todos los usuarios de una vez
        users = await user_collection.find(
            {"_id": {"$in": list(all_user_ids)}}
        ).to_list(length=len(all_user_ids))
        
        user_map = {
            str(user["_id"]): {
                "id": str(user["_id"]),
                "username": user["username"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "profile_image": user.get("profile_image")
            }
            for user in users
        }
        
        # Formatear categorías con previews
        for result in results:
            formatted_previews = []
            
            for post in result.get("preview_posts", []):
                user_id = str(post["user_id"])
                user_info = user_map.get(user_id)
                
                if user_info:
                    is_liked = ObjectId(current_user_id) in post.get("likes", [])
                    content = post["content"]
                    
                    formatted_previews.append({
                        "id": str(post["_id"]),
                        "user": user_info,
                        "content": content[:100] + "..." if len(content) > 100 else content,
                        "images": post.get("images", [])[:1],
                        "type": post["type"],
                        "skills": post.get("skills"),
                        "likes_count": post.get("likes_count", 0),
                        "comments_count": post.get("comments_count", 0),
                        "is_liked": is_liked,
                        "created_at": post["created_at"]
                    })
            
            categories_data.append({
                "skill_name": result["skill_name"],
                "posts_offering": result["posts_offering"],
                "posts_seeking": result["posts_seeking"],
                "total_posts": result["total_posts"],
                "preview_posts": formatted_previews
            })
        
        elapsed = time.time() - start_time
        logger.info(f"🔍 Categorías explore: {len(categories_data)} categorías en {elapsed:.2f}s")
        
        return {
            "categories": categories_data,
            "total_skills": len(categories_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error cargando categorías explore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/skill/{skill_name}", response_model=SkillDetailResponse)
async def get_skill_detail(
    skill_name: str,
    current_user_id: str = Depends(auth_required_depends),
    filter_type: str = Query("all", pattern="^(offering|seeking|all)$"),
    limit: int = Query(20, ge=5, le=50),
    before_id: Optional[str] = Query(None, description="ID para paginación")
):
    """
    Obtener posts detallados de una habilidad específica
    """
    try:
        if skill_name not in PREDEFINED_SKILLS:
            raise HTTPException(status_code=404, detail="Habilidad no encontrada")
        
        offering_posts = []
        seeking_posts = []
        
        pagination_query = {}
        if before_id:
            try:
                pagination_query["_id"] = {"$lt": ObjectId(before_id)}
            except:
                pass
        
        if filter_type in ["all", "offering"]:
            query_offering = {
                "type": "skill_offer",
                "skills.offering": skill_name,
                **pagination_query
            }
            
            posts_offering = await post_collection.find(query_offering)\
                .sort("created_at", -1)\
                .limit(limit)\
                .to_list(length=limit)
            
            for post in posts_offering:
                formatted = await format_post_simple(post, current_user_id)
                if formatted:
                    offering_posts.append(formatted)
        
        if filter_type in ["all", "seeking"]:
            query_seeking = {
                "type": "skill_request",
                "skills.seeking": skill_name,
                **pagination_query
            }
            
            posts_seeking = await post_collection.find(query_seeking)\
                .sort("created_at", -1)\
                .limit(limit)\
                .to_list(length=limit)
            
            for post in posts_seeking:
                formatted = await format_post_simple(post, current_user_id)
                if formatted:
                    seeking_posts.append(formatted)
        
        total_posts = len(offering_posts) + len(seeking_posts)
        has_more = total_posts >= limit
        
        logger.info(f"🎯 Skill detail '{skill_name}': {total_posts} posts")
        
        return {
            "skill_name": skill_name,
            "offering_posts": offering_posts,
            "seeking_posts": seeking_posts,
            "total_posts": total_posts,
            "has_more": has_more
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error cargando detalle de skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/search")
async def search_skills(
    query: str = Query(..., min_length=1, max_length=50),
    current_user_id: str = Depends(auth_required_depends)
):
    """
    Buscar habilidades por nombre
    """
    try:
        query_lower = query.lower()
        matching_skills = [
            skill for skill in PREDEFINED_SKILLS 
            if query_lower in skill.lower()
        ]
        
        results = []
        for skill in matching_skills[:10]:
            offering_count = await post_collection.count_documents({
                "type": "skill_offer",
                "skills.offering": skill
            })
            
            seeking_count = await post_collection.count_documents({
                "type": "skill_request",
                "skills.seeking": skill
            })
            
            results.append({
                "skill_name": skill,
                "posts_offering": offering_count,
                "posts_seeking": seeking_count,
                "total_posts": offering_count + seeking_count
            })
        
        logger.info(f"🔎 Búsqueda '{query}': {len(results)} resultados")
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )