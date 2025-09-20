from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
from app.utils.authUtils import verify_access_token
import os

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
ALGORITHM = "HS256"
security = HTTPBearer()

async def auth_required_depends(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency moderna para autenticación usando FastAPI Depends
    Usar como: async def my_route(user_id = Depends(auth_required_depends))
    """
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido - sin user_id"
        )
    
    return user_id

def auth_required(func):
    """
    Decorador para rutas que requieren autenticación
    MANTIENE COMPATIBILIDAD con código existente
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing or invalid",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = auth_header.replace("Bearer ", "")
        payload = verify_access_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido - sin user_id"
            )
        
        request.state.user = {
            "user_id": user_id,
            "payload": payload
        }
        
        return await func(*args, **kwargs)
    
    return wrapper

def get_current_user(request: Request):
    """
    Helper para obtener el usuario actual desde el request
    """
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    return request.state.user