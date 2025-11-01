from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
ALGORITHM = "HS256"

def create_access_token(data: dict):
    """Crea un access token que expira en 2 horas"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=2)  # 2 horas 
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """Crea un refresh token que expira en 30 días"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)  # 30 días
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str):
    """Verifica y decodifica un access token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verificar que es un access token
        if payload.get("type") != "access":
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except JWTError:
        return None

def verify_refresh_token(token: str):
    """Verifica y decodifica un refresh token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verificar que es un refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Tipo de token inválido")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expirado. Por favor inicia sesión de nuevo")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

def create_token_pair(user_data: dict):
    """Crea ambos tokens para un usuario"""
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 7200  # 2 horas en segundos
    }

# Funciones de compatibilidad con tu código existente
def decode_token(token: str):
    """DEPRECATED: Usar verify_access_token en su lugar"""
    return verify_access_token(token)

def get_user_id_from_token(token: str):
    """Extrae el user_id de un access token"""
    payload = verify_access_token(token)
    if payload:
        return payload.get("sub")
    return None