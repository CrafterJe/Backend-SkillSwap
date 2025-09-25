import sys
import os

# Añade la carpeta raíz del proyecto (backend) al path para que funcione el import "app"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from app.routes import auth
from app.routes.navigation.profileTabRoute import profileSettingsRoute
from app.routes.navigation.profileTabRoute import profileScreenRoute
from app.routes.navigation.searchRoute import router as search_router
from app.routes.navigation import notificationsRoute
from app.routes import messageRoute
from app.routes import websocketRoute
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

# Rutas existentes
app.include_router(auth.router)
app.include_router(profileSettingsRoute.router)
app.include_router(profileScreenRoute.router)
app.include_router(search_router)
app.include_router(notificationsRoute.router)
app.include_router(messageRoute.router)
app.include_router(websocketRoute.router)

# Punto de entrada 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="192.168.100.15", port=8000, reload=True)