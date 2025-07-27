import re
from pydantic import BaseModel, EmailStr, field_validator
from .models import UserRole
from datetime import date

# Propiedades base que se comparten
class UserBase(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str
    fecha_nacimiento: date
    carrera: str | None = None
    grupo: str | None = None

    @field_validator('email')
    @classmethod
    def validate_uptc_email(cls, v: str) -> str:
        if not v.endswith('@uptc.edu.co'):
            raise ValueError('Debe ser un correo institucional @uptc.edu.co')
        return v

# Esquema para CREAR un usuario (lo que recibe la API)
class UserCreate(UserBase):
    password: str
    registration_token: str

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Valida que la contraseña tenga al menos 8 caracteres, una mayúscula,
        una minúscula, un número y un carácter especial.
        """
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula.')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula.')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número.')
        if not re.search(r'[@$!%*?&,./]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (@$!%*?&,./).')
        return v

# Esquema para LEER un usuario (lo que devuelve la API)
class User(UserBase):
    id: int
    is_active: bool
    rol: UserRole

    class Config:
        from_attributes = True