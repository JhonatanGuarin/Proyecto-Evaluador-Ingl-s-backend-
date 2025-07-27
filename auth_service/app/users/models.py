import enum
from sqlalchemy import Boolean, Column, Integer, String, Enum, Date, DateTime
from ..core.db import Base

# Define los roles usando un Enum de Python
class UserRole(str, enum.Enum):
    SUPERADMIN = "SuperAdmin"
    PROFESOR = "profesor"
    ESTUDIANTE = "estudiante"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    carrera = Column(String, nullable=True) # Puede ser nulo para profesores/admins
    grupo = Column(String, nullable=True)   # Puede ser nulo para profesores/admins

    # --- Campo de Rol ---
    rol = Column(Enum(UserRole), nullable=False, default=UserRole.ESTUDIANTE)
    is_active = Column(Boolean, default=True)

    password_reset_code = Column(String, nullable=True)
    password_reset_expires_at = Column(DateTime, nullable=True)