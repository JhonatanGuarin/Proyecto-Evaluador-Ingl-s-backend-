# auth_service/app/main.py

from fastapi import FastAPI, Depends
from .core.db import engine
from .users import models as user_models
from .auth import routes as auth_routes
from .users import routes as user_routes


# Crea las tablas en la base de datos
user_models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Microservicio de Autenticación",
    description="API para gestionar usuarios y autenticación con JWT.",
    version="1.0.0",
    openapi_version="3.1.0",
    root_path="/auth" 
)

# Incluir las rutas de usuarios
app.include_router(user_routes.router, prefix="/users", tags=["Users"])

# Incluir las rutas de autenticación
app.include_router(auth_routes.router, tags=["Authentication"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenido al Microservicio de Autenticación"}