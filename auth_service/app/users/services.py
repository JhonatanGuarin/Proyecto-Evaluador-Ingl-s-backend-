from sqlalchemy.orm import Session
from . import models, schemas
from ..auth import services as auth_services

def get_user_by_email(db: Session, email: str):
    """
    Busca un usuario en la base de datos por su email.
    """
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """
    Crea un nuevo usuario en la base de datos.
    """
    hashed_password = auth_services.get_password_hash(user.password)
    
    # Crea la instancia del modelo User con los datos del esquema
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        nombre=user.nombre,
        apellido=user.apellido,
        fecha_nacimiento=user.fecha_nacimiento,
        carrera=user.carrera,
        grupo=user.grupo,
        # El rol se asigna por defecto en el modelo
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user