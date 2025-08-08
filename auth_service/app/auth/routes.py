from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError

from ..core import db
from ..core.config import settings
from ..core.email import send_reset_password_email, send_verification_email
from ..users import schemas as user_schemas, services as user_services
from . import models as auth_models, schemas as auth_schemas, services as auth_services
from fastapi.responses import JSONResponse

from fastapi import Depends
from .dependencies import get_current_user
from ..users.models import User
from fastapi import Request


router = APIRouter()

@router.post("/register", response_model=user_schemas.User)
def register_user(user: user_schemas.UserCreate, db: Session = Depends(db.get_db)):
    try:
        payload = jwt.decode(
            user.registration_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("scope") != "registration" or payload.get("sub") != user.email:
            raise HTTPException(status_code=400, detail="Token de registro inválido")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token de registro inválido o expirado")

    db_user = user_services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    return user_services.create_user(db=db, user=user)

# --- AÑADIR ESTOS DOS NUEVOS ENDPOINTS ANTES DE /token ---

@router.post("/request-verification")
async def request_verification(
    request: auth_schemas.RequestVerificationSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db.get_db)
):
    if user_services.get_user_by_email(db, email=request.email):
        raise HTTPException(status_code=400, detail="El correo ya está en uso")

    code = auth_services.generate_reset_code()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    verification_entry = db.query(auth_models.EmailVerification).filter(auth_models.EmailVerification.email == request.email).first()
    if verification_entry:
        verification_entry.code = code
        verification_entry.expires_at = expires_at
    else:
        verification_entry = auth_models.EmailVerification(email=request.email, code=code, expires_at=expires_at)
    
    db.add(verification_entry)
    db.commit()

    background_tasks.add_task(send_verification_email, email_to=request.email, verification_code=code)
    return {"message": "Se ha enviado un código de verificación a tu correo."}


@router.post("/verify-code", response_model=auth_schemas.VerificationSuccessSchema)
def verify_code(request: auth_schemas.VerifyCodeSchema, db: Session = Depends(db.get_db)):
    verification_entry = db.query(auth_models.EmailVerification).filter(
        auth_models.EmailVerification.email == request.email,
        auth_models.EmailVerification.code == request.code
    ).first()

    if not verification_entry or datetime.utcnow() > verification_entry.expires_at:
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    
    # El código es válido, genera el token de registro
    registration_token = auth_services.create_registration_token(email=request.email)
    
    # Limpia el código para que no se pueda reusar
    db.delete(verification_entry)
    db.commit()

    return {
        "registration_token": registration_token,
        "message": "Correo verificado exitosamente. Ahora puedes completar tu registro."
    }


@router.post("/token")
def login_for_access_token(
    db: Session = Depends(db.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = user_services.get_user_by_email(db, email=form_data.username)
    if not user or not auth_services.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_services.create_access_token(
        data={"sub": user.email, "rol": user.rol.value}
    )

    response = JSONResponse(content={"message": "Login exitoso", "token": access_token})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # ✅ pon esto en True en producción con HTTPS
        samesite="Lax",
        max_age=1800,
        path="/"
    )
    return response

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email}


@router.post("/logout")
def logout(request: Request):
    token = request.cookies.get("access_token")
    print(f"Token que se eliminará: {token}")
    response = JSONResponse(content={"message": "Sesión cerrada"})
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=True,      # Igual que en login
        samesite="Lax"    # Igual que en login
    )
    return response




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