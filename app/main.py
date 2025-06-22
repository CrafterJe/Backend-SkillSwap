import sys
import os

# Añade la carpeta raíz del proyecto (backend) al path para que funcione el import "app"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from app.routes import auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas de autenticación
app.include_router(auth.router)

# Punto de entrada 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="192.168.100.11", port=8000, reload=True)
