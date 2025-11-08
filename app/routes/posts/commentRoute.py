# app/routes/posts/commentRoute.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.schemas.posts.postSchema import CommentCreate, CommentResponse, CommentsListResponse, PostUser
from app.utils.auth_guardUtils import auth_required_depends
from app.database import comment_collection, post_collection, user_collection, notification_collection
from app.utils.push_notifications import send_push_notification
from bson import ObjectId
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts/{post_id}/comments", tags=["Comments"])

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user_id: str = Depends(auth_required_depends)
):
    """Crear un comentario en un post"""
    try:
        # Verificar que el post existe
        post = await post_collection.find_one({"_id": ObjectId(post_id)})
        
        if not post:
            raise HTTPException(status_code=404, detail="Post no encontrado")
        
        # Obtener info del usuario actual
        current_user = await user_collection.find_one({"_id": ObjectId(current_user_id)})
        
        # Crear comentario
        comment_dict = {
            "post_id": ObjectId(post_id),
            "user_id": ObjectId(current_user_id),
            "content": comment_data.content,
            "created_at": datetime.utcnow()
        }
        
        result = await comment_collection.insert_one(comment_dict)
        
        # Incrementar contador de comentarios en el post
        await post_collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"comments_count": 1}}
        )
        
        # Crear notificación solo si no es tu propio post
        if str(post["user_id"]) != current_user_id:
            await notification_collection.insert_one({
                "to_user": post["user_id"],
                "from_user": ObjectId(current_user_id),
                "type": "comment",
                "post_id": ObjectId(post_id),
                "comment_id": result.inserted_id,
                "message": f"{current_user['username']} comentó tu publicación",
                "created_at": datetime.utcnow(),
                "read": False
            })
            
            # Enviar push notification
            post_owner = await user_collection.find_one({"_id": post["user_id"]})
            if post_owner.get("expo_push_token"):
                await send_push_notification(
                    token=post_owner["expo_push_token"],
                    title="Nuevo comentario",
                    body=f"{current_user['username']}: {comment_data.content[:50]}...",
                    data={
                        "type": "comment",
                        "post_id": post_id,
                        "from_user": current_user_id
                    }
                )
        
        logger.info(f"💬 Comentario creado en post {post_id}")
        
        return {
            "id": str(result.inserted_id),
            "user": {
                "id": str(current_user["_id"]),
                "username": current_user["username"],
                "first_name": current_user.get("first_name", ""),
                "last_name": current_user.get("last_name", ""),
                "profile_image": current_user.get("profile_image")
            },
            "content": comment_data.content,
            "created_at": comment_dict["created_at"]
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error creando comentario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/", response_model=CommentsListResponse)
async def get_comments(
    post_id: str,
    current_user_id: str = Depends(auth_required_depends),
    limit: int = Query(20, ge=5, le=50, description="Número de comentarios a cargar"),
    before_id: str = Query(None, description="ID del comentario para paginación")
):
    """Obtener comentarios de un post"""
    try:
        # Verificar que el post existe
        post = await post_collection.find_one({"_id": ObjectId(post_id)})
        
        if not post:
            raise HTTPException(status_code=404, detail="Post no encontrado")
        
        # Query con paginación
        query = {"post_id": ObjectId(post_id)}
        
        if before_id:
            try:
                query["_id"] = {"$lt": ObjectId(before_id)}
            except:
                pass
        
        # Obtener comentarios
        comments = await comment_collection.find(query)\
            .sort("created_at", -1)\
            .limit(limit + 1)\
            .to_list(length=limit + 1)
        
        has_more = len(comments) > limit
        if has_more:
            comments = comments[:limit]
        
        # Obtener info de usuarios (optimizado)
        user_ids = list(set(comment["user_id"] for comment in comments))
        users = await user_collection.find(
            {"_id": {"$in": user_ids}}
        ).to_list(length=len(user_ids))
        
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
        
        # Formatear comentarios
        formatted_comments = []
        for comment in comments:
            user_id = str(comment["user_id"])
            user_info = user_map.get(user_id)
            
            if user_info:
                formatted_comments.append({
                    "id": str(comment["_id"]),
                    "user": user_info,
                    "content": comment["content"],
                    "created_at": comment["created_at"]
                })
        
        # Invertir para orden cronológico
        formatted_comments.reverse()
        
        logger.info(f"💬 Comentarios cargados: {len(formatted_comments)} del post {post_id}")
        
        return {
            "comments": formatted_comments,
            "count": len(formatted_comments),
            "has_more": has_more
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error cargando comentarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.delete("/{comment_id}")
async def delete_comment(
    post_id: str,
    comment_id: str,
    current_user_id: str = Depends(auth_required_depends)
):
    """Eliminar un comentario (solo el dueño)"""
    try:
        # Buscar comentario
        comment = await comment_collection.find_one({"_id": ObjectId(comment_id)})
        
        if not comment:
            raise HTTPException(status_code=404, detail="Comentario no encontrado")
        
        # Verificar que sea el dueño
        if str(comment["user_id"]) != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar este comentario"
            )
        
        # Eliminar comentario
        await comment_collection.delete_one({"_id": ObjectId(comment_id)})
        
        # Decrementar contador de comentarios
        await post_collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"comments_count": -1}}
        )
        
        # Eliminar notificación asociada
        await notification_collection.delete_many({
            "comment_id": ObjectId(comment_id)
        })
        
        logger.info(f"🗑️ Comentario eliminado: {comment_id}")
        
        return {"message": "Comentario eliminado exitosamente"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error eliminando comentario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )