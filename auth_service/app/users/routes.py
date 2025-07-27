from fastapi import APIRouter, Depends
from .schemas import User
from ..auth.dependencies import get_current_user

router = APIRouter()

@router.get("/me", response_model=User, tags=["Users"])
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Obtiene los datos del usuario actualmente autenticado.
    """
    return current_user