from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv

load_dotenv()

# Tu CLIENT_ID de Google Cloud Console
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

async def verify_google_token(token: str) -> dict:
    """
    Verifica un ID token de Google y retorna la información del usuario
    
    Args:
        token: ID token de Google
        
    Returns:
        dict con: email, name, given_name, family_name, picture, sub (google_id)
        
    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        # Verificar el token con Google
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Verificar que el token es de Google
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Token no es de Google')
        
        return {
            'email': idinfo.get('email'),
            'email_verified': idinfo.get('email_verified', False),
            'name': idinfo.get('name', ''),
            'given_name': idinfo.get('given_name', ''),
            'family_name': idinfo.get('family_name', ''),
            'picture': idinfo.get('picture', ''),
            'google_id': idinfo.get('sub'),  # ID único de Google
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de Google inválido: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error al verificar token de Google: {str(e)}"
        )