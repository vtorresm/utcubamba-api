from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.security import verify_password, get_password_hash, create_access_token
from src.db.database import get_db
from src.models.schemas import LoginRequest
from src.models.database_models import User as UserModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/token")
def login_for_access_token(login_data: LoginRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"JSON login attempt for user: {login_data.email}")
        user = db.query(UserModel).filter(UserModel.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Invalid credentials for user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.info(f"Generating tokens for user: {user.email}")
        access_token = create_access_token(data={"sub": user.email, "role": user.role})
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al generar el token de acceso"
            )
        
        logger.info(f"Login successful for user: {user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active
            }
        }
    except HTTPException as he:
        logger.error(f"HTTP Exception during login: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al procesar el inicio de sesión"
        )