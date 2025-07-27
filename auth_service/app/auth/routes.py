from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..core import db
from ..core.email import send_reset_password_email
from ..users import schemas as user_schemas, services as user_services
from . import schemas as auth_schemas, services as auth_services

router = APIRouter()

@router.post("/register", response_model=user_schemas.User)
def register_user(user: user_schemas.UserCreate, db: Session = Depends(db.get_db)):
    db_user = user_services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return user_services.create_user(db=db, user=user)

@router.post("/token", response_model=auth_schemas.Token)
def login_for_access_token(db: Session = Depends(db.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_services.get_user_by_email(db, email=form_data.username)
    if not user or not auth_services.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crea el token con el email (sub) y el rol
    access_token = auth_services.create_access_token(
        data={"sub": user.email, "rol": user.rol.value} # <-- MODIFICACIÓN CLAVE
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(
    request: auth_schemas.ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db.get_db)
):
    user = user_services.get_user_by_email(db, email=request.email)
    if user:
        # Generar código y fecha de expiración
        reset_code = auth_services.generate_reset_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Guardar en la base de datos
        user.password_reset_code = reset_code
        user.password_reset_expires_at = expires_at
        db.commit()

        # Enviar correo en segundo plano
        background_tasks.add_task(
            send_reset_password_email, email_to=user.email, reset_code=reset_code
        )
    
    return {"message": "Si tu correo está registrado, recibirás un código para resetear tu contraseña."}


@router.post("/reset-password")
def reset_password(request: auth_schemas.ResetPasswordSchema, db: Session = Depends(db.get_db)):
    user = user_services.get_user_by_email(db, email=request.email)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if (
        not user.password_reset_code
        or user.password_reset_code != request.code
        or datetime.utcnow() > user.password_reset_expires_at
    ):
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    
    # Actualizar contraseña
    user.hashed_password = auth_services.get_password_hash(request.new_password)
    
    # Limpiar campos de reseteo
    user.password_reset_code = None
    user.password_reset_expires_at = None
    db.commit()

    return {"message": "Contraseña actualizada exitosamente."}