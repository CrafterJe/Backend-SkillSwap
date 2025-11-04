from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.schemas.posts.postSchema import PostCreate, PostUpdate, PostResponse, LikeResponse, PostUser
from app.utils.auth_guardUtils import auth_required_depends
from app.database import post_collection, user_collection, notification_collection
from app.utils.push_notifications import send_push_notification
from bson import ObjectId
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["Posts"])

# Helper para formatear posts
async def format_post(post: dict, current_user_id: str) -> dict:
    """Formatea un post con información del usuario"""
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
        "content": post["content"],
        "images": post.get("images", []),
        "type": post["type"],
        "skills": post.get("skills"),
        "likes_count": post.get("likes_count", 0),
        "comments_count": post.get("comments_count", 0),
        "is_liked": is_liked,
        "created_at": post["created_at"],
        "updated_at": post["updated_at"]
    }

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user_id: str = Depends(auth_required_depends)
):
    """Crear un nuevo post"""
    try:
        # Validar que si es post de habilidad, tenga skills
        if post_data.type in ["skill_offer", "skill_request"] and not post_data.skills:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los posts de tipo skill_offer o skill_request deben incluir habilidades"
            )
        
        post_dict = {
            "user_id": ObjectId(current_user_id),
            "content": post_data.content,
            "images": post_data.images,
            "type": post_data.type,
            "skills": post_data.skills.dict() if post_data.skills else None,
            "likes": [],
            "likes_count": 0,
            "comments_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await post_collection.insert_one(post_dict)
        
        logger.info(f"✅ Post creado: {str(result.inserted_id)} por usuario {current_user_id}")
        
        return {
            "message": "Post creado exitosamente",
            "post_id": str(result.inserted_id)
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error creando post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/feed", response_model=List[PostResponse])
async def get_feed(
    current_user_id: str = Depends(auth_required_depends),
    limit: int = Query(20, ge=5, le=50, description="Número de posts a cargar"),
    before_id: str = Query(None, description="ID del post para paginación")
):
    """Obtener feed de posts de usuarios que sigues"""
    try:
        # Obtener usuario actual
        current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
        following_ids = current_user.get("following", [])
        
        # Incluir posts propios
        following_ids.append(ObjectId(current_user_id))
        
        # Query con paginación
        query = {"user_id": {"$in": following_ids}}
        
        if before_id:
            try:
                query["_id"] = {"$lt": ObjectId(before_id)}
            except:
                pass
        
        # Obtener posts
        posts = await post_collection.find(query)\
            .sort("created_at", -1)\
            .limit(limit)\
            .to_list(length=limit)
        
        # Formatear posts
        formatted_posts = []
        for post in posts:
            formatted = await format_post(post, current_user_id)
            if formatted:
                formatted_posts.append(formatted)
        
        logger.info(f"📰 Feed cargado: {len(formatted_posts)} posts para usuario {current_user_id}")
        
        return formatted_posts
        
    except Exception as e:
        logger.error(f"❌ Error cargando feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/explore", response_model=List[PostResponse])
async def get_explore(
    current_user_id: str = Depends(auth_required_depends),
    limit: int = Query(20, ge=5, le=50, description="Número de posts a cargar"),
    before_id: str = Query(None, description="ID del post para paginación")
):
    """Obtener posts de exploración (todos los posts públicos)"""
    try:
        # Query con paginación
        query = {}
        
        if before_id:
            try:
                query["_id"] = {"$lt": ObjectId(before_id)}
            except:
                pass
        
        # Obtener posts ordenados por engagement y fecha
        posts = await post_collection.find(query)\
            .sort([("likes_count", -1), ("created_at", -1)])\
            .limit(limit)\
            .to_list(length=limit)
        
        # Formatear posts
        formatted_posts = []
        for post in posts:
            formatted = await format_post(post, current_user_id)
            if formatted:
                formatted_posts.append(formatted)
        
        logger.info(f"🔍 Explore cargado: {len(formatted_posts)} posts")
        
        return formatted_posts
        
    except Exception as e:
        logger.error(f"❌ Error cargando explore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/user/{username}", response_model=List[PostResponse])
async def get_user_posts(
    username: str,
    current_user_id: str = Depends(auth_required_depends),
    limit: int = Query(20, ge=5, le=50, description="Número de posts a cargar"),
    before_id: str = Query(None, description="ID del post para paginación")
):
    """Obtener posts de un usuario específico"""
    try:
        # Buscar usuario
        user = await user_collection.find_one({
            "username": {"$regex": f"^{username}$", "$options": "i"}
        })
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Query con paginación
        query = {"user_id": user["_id"]}
        
        if before_id:
            try:
                query["_id"] = {"$lt": ObjectId(before_id)}
            except:
                pass
        
        # Obtener posts
        posts = await post_collection.find(query)\
            .sort("created_at", -1)\
            .limit(limit)\
            .to_list(length=limit)
        
        # Formatear posts
        formatted_posts = []
        for post in posts:
            formatted = await format_post(post, current_user_id)
            if formatted:
                formatted_posts.append(formatted)
        
        logger.info(f"👤 Posts de {username}: {len(formatted_posts)} posts")
        
        return formatted_posts
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error cargando posts de usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.post("/{post_id}/like", response_model=LikeResponse)
async def toggle_like(
    post_id: str,
    current_user_id: str = Depends(auth_required_depends)
):
    """Dar o quitar like a un post"""
    try:
        # Buscar post
        post = await post_collection.find_one({"_id": ObjectId(post_id)})
        
        if not post:
            raise HTTPException(status_code=404, detail="Post no encontrado")
        
        user_obj_id = ObjectId(current_user_id)
        likes = post.get("likes", [])
        
        # Toggle like
        if user_obj_id in likes:
            # Quitar like
            await post_collection.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$pull": {"likes": user_obj_id},
                    "$inc": {"likes_count": -1}
                }
            )
            
            # Eliminar notificación
            await notification_collection.delete_many({
                "to_user": post["user_id"],
                "from_user": user_obj_id,
                "type": "like",
                "post_id": ObjectId(post_id)
            })
            
            logger.info(f"💔 Like removido del post {post_id}")
            
            return {
                "message": "Like removido",
                "is_liked": False,
                "likes_count": post.get("likes_count", 1) - 1
            }
        else:
            # Dar like
            await post_collection.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$push": {"likes": user_obj_id},
                    "$inc": {"likes_count": 1}
                }
            )
            
            # Crear notificación solo si no es tu propio post
            if str(post["user_id"]) != current_user_id:
                current_user = await user_collection.find_one({"_id": user_obj_id})
                
                await notification_collection.insert_one({
                    "to_user": post["user_id"],
                    "from_user": user_obj_id,
                    "type": "like",
                    "post_id": ObjectId(post_id),
                    "message": f"{current_user['username']} le dio like a tu publicación",
                    "created_at": datetime.utcnow(),
                    "read": False
                })
                
                # Enviar push notification
                post_owner = await user_collection.find_one({"_id": post["user_id"]})
                if post_owner.get("expo_push_token"):
                    await send_push_notification(
                        token=post_owner["expo_push_token"],
                        title="¡Nuevo like!",
                        body=f"{current_user['username']} le dio like a tu publicación",
                        data={
                            "type": "like",
                            "post_id": post_id,
                            "from_user": current_user_id
                        }
                    )
            
            logger.info(f"❤️ Like agregado al post {post_id}")
            
            return {
                "message": "Like agregado",
                "is_liked": True,
                "likes_count": post.get("likes_count", 0) + 1
            }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error toggle like: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user_id: str = Depends(auth_required_depends)
):
    """Eliminar un post (solo el dueño)"""
    try:
        # Buscar post
        post = await post_collection.find_one({"_id": ObjectId(post_id)})
        
        if not post:
            raise HTTPException(status_code=404, detail="Post no encontrado")
        
        # Verificar que sea el dueño
        if str(post["user_id"]) != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar este post"
            )
        
        # Eliminar post
        await post_collection.delete_one({"_id": ObjectId(post_id)})
        
        # Eliminar notificaciones asociadas
        await notification_collection.delete_many({"post_id": ObjectId(post_id)})
        
        # Eliminar comentarios asociados (cuando implementemos comentarios)
        from app.database import comment_collection
        await comment_collection.delete_many({"post_id": ObjectId(post_id)})
        
        logger.info(f"🗑️ Post eliminado: {post_id}")
        
        return {"message": "Post eliminado exitosamente"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error eliminando post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.put("/{post_id}", response_model=dict)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_user_id: str = Depends(auth_required_depends)
):
    """Actualizar un post (solo el dueño)"""
    try:
        # Buscar post
        post = await post_collection.find_one({"_id": ObjectId(post_id)})
        
        if not post:
            raise HTTPException(status_code=404, detail="Post no encontrado")
        
        # Verificar que sea el dueño
        if str(post["user_id"]) != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para editar este post"
            )
        
        # Preparar datos para actualizar
        update_data = {"updated_at": datetime.utcnow()}
        
        if post_data.content is not None:
            update_data["content"] = post_data.content
        if post_data.images is not None:
            update_data["images"] = post_data.images
        if post_data.type is not None:
            update_data["type"] = post_data.type
        if post_data.skills is not None:
            update_data["skills"] = post_data.skills.dict()
        
        # Actualizar post
        await post_collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": update_data}
        )
        
        logger.info(f"✏️ Post actualizado: {post_id}")
        
        return {"message": "Post actualizado exitosamente"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error actualizando post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )