from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.user import User
from src.services.auth_service import AuthService

# Reutilizar el mismo OAuth2PasswordBearer que está en AuthService
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency function that gets the current authenticated user.
    This uses the token from the request and the database session to authenticate the user.
    
    Args:
        token: The JWT token from the request
        db: The database session
        
    Returns:
        The authenticated User object
        
    Raises:
        HTTPException: If authentication fails
    """
    return AuthService.get_current_user(db=db, token=token)

