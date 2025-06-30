# routes/searchRoute.py
from fastapi import APIRouter, Query, HTTPException
from app.database import user_collection
from bson import ObjectId
from typing import List
from app.schemas.navigation.searchSchema import SearchUserResult
import re

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
    
    # Ordenar resultados por relevancia:
    # 1. Coincidencias exactas en username
    # 2. Coincidencias que empiecen con el query en username
    # 3. Coincidencias en first_name
    # 4. Coincidencias en last_name
    # 5. Otras coincidencias
    def sort_relevance(user):
        username = user.get("username", "").lower()
        first_name = user.get("first_name", "").lower()
        last_name = user.get("last_name", "").lower()
        query_lower = query.lower()
        
        # Coincidencia exacta en username
        if username == query_lower:
            return 0
        # Empieza con el query en username
        elif username.startswith(query_lower):
            return 1
        # Coincidencia exacta en first_name
        elif first_name == query_lower:
            return 2
        # Empieza con el query en first_name
        elif first_name.startswith(query_lower):
            return 3
        # Contiene el query en username
        elif query_lower in username:
            return 4
        # Contiene el query en first_name
        elif query_lower in first_name:
            return 5
        # Contiene el query en last_name
        elif query_lower in last_name:
            return 6
        # Otras coincidencias
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