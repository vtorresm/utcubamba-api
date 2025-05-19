from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.services.auth_service import AuthService
from src.models.user import Role
from datetime import timedelta
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

router = APIRouter()

# Modelos para las solicitudes
class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = Role.USER

class ResetPasswordRequest(BaseModel):
    email: str

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str

@router.post("/login", tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Inicia sesión y devuelve un token JWT.
    """
    user = AuthService.verify_user(db, form_data.username, form_data.password)  # form_data.username es el email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", tags=["auth"])
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario.
    """
    user = AuthService.register_user(db, request.email, request.password, request.role)
    return {"message": "User registered successfully", "email": user.email, "role": user.role}

@router.post("/password-reset", tags=["auth"])
def request_password_reset(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Solicita un token para restablecer la contraseña.
    """
    token = AuthService.generate_reset_token(db, request.email)
    return {"message": "Password reset token generated", "token": token}

@router.post("/password-reset/confirm", tags=["auth"])
def reset_password(request: ResetPasswordConfirm, db: Session = Depends(get_db)):
    """
    Restablece la contraseña usando un token.
    """
    AuthService.reset_password(db, request.token, request.new_password)
    return {"message": "Password reset successfully"}