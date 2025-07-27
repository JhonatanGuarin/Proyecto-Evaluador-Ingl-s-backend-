from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from ..core.config import settings
import secrets
import string


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def generate_reset_code(length: int = 6) -> str:
    """
    Genera un código numérico seguro.
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))