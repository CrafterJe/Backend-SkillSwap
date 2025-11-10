# routes/searchRoute.py
from fastapi import APIRouter, Query, HTTPException, Depends
from app.database import user_collection, search_history_collection
from bson import ObjectId
from typing import List
from app.schemas.navigation.searchSchema import (
    SearchUserResult, 
    SearchHistoryCreate, 
    UserHistoryCreate,
    SearchHistoryResponse
)
from app.utils.auth_guardUtils import auth_required_depends
import re
from datetime import datetime

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

@router.get("/users", response_model=List[SearchUserResult])
async def search_users(query: str = Query(..., min_length=2, max_length=50)):
    # Escapar caracteres especiales de regex para evitar errores
    escaped_query = re.escape(query)
    
    # Crear regex case-insensitive que busque el término al inicio o como parte de la palabra
    regex_pattern = f".*{escaped_query}.*"
    
    # Primero intentar búsqueda con regex (más flexible)
    search_filter = {
        "$or": [
            {"username": {"$regex": regex_pattern, "$options": "i"}},
            {"first_name": {"$regex": regex_pattern, "$options": "i"}},
            {"last_name": {"$regex": regex_pattern, "$options": "i"}}
        ]
    }
    
    # Proyección para obtener solo los campos necesarios
    projection = {
        "username": 1,
        "first_name": 1,
        "last_name": 1,
        "profile_image": 1
    }
    
    # Ejecutar búsqueda con regex
    results_cursor = user_collection.find(search_filter, projection)
    results = await results_cursor.to_list(length=15)
    
    # Si no hay resultados con regex, intentar búsqueda de texto completo
    if not results:
        try:
            text_search_filter = {"$text": {"$search": query}}
            text_results_cursor = user_collection.find(text_search_filter, projection)
            results = await text_results_cursor.to_list(length=15)
        except Exception:
            # Si falla la búsqueda de texto, mantener lista vacía
            results = []
    
    # Ordenar resultados por relevancia
    def sort_relevance(user):
        username = user.get("username", "").lower()
        first_name = user.get("first_name", "").lower()
        last_name = user.get("last_name", "").lower()
        query_lower = query.lower()
        
        if username == query_lower:
            return 0
        elif username.startswith(query_lower):
            return 1
        elif first_name == query_lower:
            return 2
        elif first_name.startswith(query_lower):
            return 3
        elif query_lower in username:
            return 4
        elif query_lower in first_name:
            return 5
        elif query_lower in last_name:
            return 6
        else:
            return 7
    
    # Ordenar por relevancia
    sorted_results = sorted(results, key=sort_relevance)
    
    # Limitar a 10 resultados finales
    final_results = sorted_results[:10]
    
    return [
        {
            "id": str(user["_id"]),
            "username": user["username"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "profile_image": user.get("profile_image")
        }
        for user in final_results
    ]

# ==================== ENDPOINTS DE HISTORIAL ====================

@router.post("/history/query", status_code=201)
async def save_query_to_history(
    search_data: SearchHistoryCreate,
    current_user_id: str = Depends(auth_required_depends)
):
    """Guarda una búsqueda de texto (query) en el historial"""
    # Verificar si ya existe esta búsqueda para este usuario
    existing = await search_history_collection.find_one({
        "user_id": current_user_id,
        "type": "query",
        "query": search_data.query
    })
    
    if existing:
        # Si ya existe, actualizar el timestamp
        await search_history_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {"searched_at": datetime.utcnow()}}
        )
        return {"message": "Historial actualizado"}
    
    # Verificar si el usuario ya tiene 20 items en historial
    count = await search_history_collection.count_documents({"user_id": current_user_id})
    
    if count >= 20:
        # Eliminar el item más antiguo
        oldest = await search_history_collection.find_one(
            {"user_id": current_user_id},
            sort=[("searched_at", 1)]
        )
        if oldest:
            await search_history_collection.delete_one({"_id": oldest["_id"]})
    
    # Guardar nueva búsqueda
    search_history = {
        "user_id": current_user_id,
        "type": "query",
        "query": search_data.query,
        "clicked_user_id": None,
        "searched_at": datetime.utcnow()
    }
    
    await search_history_collection.insert_one(search_history)
    
    return {"message": "Búsqueda guardada en historial"}

@router.post("/history/user", status_code=201)
async def save_user_to_history(
    user_data: UserHistoryCreate,
    current_user_id: str = Depends(auth_required_depends)
):
    """Guarda un usuario clickeado en el historial"""
    # Verificar que el usuario exista
    clicked_user = await user_collection.find_one({"_id": ObjectId(user_data.user_id)})
    
    if not clicked_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar si ya existe este usuario en el historial
    existing = await search_history_collection.find_one({
        "user_id": current_user_id,
        "type": "user",
        "clicked_user_id": ObjectId(user_data.user_id)
    })
    
    if existing:
        # Si ya existe, actualizar el timestamp
        await search_history_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {"searched_at": datetime.utcnow()}}
        )
        return {"message": "Historial actualizado"}
    
    # Verificar si el usuario ya tiene 20 items en historial
    count = await search_history_collection.count_documents({"user_id": current_user_id})
    
    if count >= 20:
        # Eliminar el item más antiguo
        oldest = await search_history_collection.find_one(
            {"user_id": current_user_id},
            sort=[("searched_at", 1)]
        )
        if oldest:
            await search_history_collection.delete_one({"_id": oldest["_id"]})
    
    # Guardar usuario en historial
    user_history = {
        "user_id": current_user_id,
        "type": "user",
        "query": None,
        "clicked_user_id": ObjectId(user_data.user_id),
        "searched_at": datetime.utcnow()
    }
    
    await search_history_collection.insert_one(user_history)
    
    return {"message": "Usuario guardado en historial"}

@router.get("/history", response_model=List[SearchHistoryResponse])
async def get_search_history(current_user_id: str = Depends(auth_required_depends)):
    """Obtiene el historial de búsquedas del usuario (queries + usuarios)"""
    # Obtener historial ordenado por fecha (más reciente primero)
    cursor = search_history_collection.find(
        {"user_id": current_user_id}
    ).sort("searched_at", -1).limit(20)
    
    history = await cursor.to_list(length=20)
    
    result = []
    
    for item in history:
        if item["type"] == "query":
            # Item de tipo query
            result.append({
                "id": str(item["_id"]),
                "user_id": item["user_id"],
                "type": "query",
                "query": item["query"],
                "clicked_user": None,
                "searched_at": item["searched_at"]
            })
        else:
            # Item de tipo user - obtener info del usuario
            clicked_user = await user_collection.find_one({"_id": item["clicked_user_id"]})
            
            if clicked_user:
                result.append({
                    "id": str(item["_id"]),
                    "user_id": item["user_id"],
                    "type": "user",
                    "query": None,
                    "clicked_user": {
                        "id": str(clicked_user["_id"]),
                        "username": clicked_user["username"],
                        "first_name": clicked_user["first_name"],
                        "last_name": clicked_user["last_name"],
                        "profile_image": clicked_user.get("profile_image")
                    },
                    "searched_at": item["searched_at"]
                })
    
    return result

@router.delete("/history/{history_id}")
async def delete_search_history_item(
    history_id: str,
    current_user_id: str = Depends(auth_required_depends)
):
    """Elimina un item específico del historial (query o usuario)"""
    result = await search_history_collection.delete_one({
        "_id": ObjectId(history_id),
        "user_id": current_user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado en el historial")
    
    return {"message": "Item eliminado del historial"}

@router.delete("/history")
async def clear_search_history(current_user_id: str = Depends(auth_required_depends)):
    """Limpia todo el historial de búsquedas del usuario"""
    result = await search_history_collection.delete_many({"user_id": current_user_id})
    
    return {
        "message": "Historial limpiado",
        "deleted_count": result.deleted_count
    }