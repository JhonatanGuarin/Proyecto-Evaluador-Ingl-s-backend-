import re
from pydantic import BaseModel, EmailStr, field_validator
from ..users.models import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr | None = None
    rol: UserRole | None = None 
    


class ForgotPasswordSchema(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    email: EmailStr
    code: str
    new_password: str
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
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
