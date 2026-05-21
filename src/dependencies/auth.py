from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.user import User
from src.services.auth_service import AuthService

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

def get_current_user(
    request: Request,
    header_token: str | None = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = header_token or request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthService.get_current_user(db=db, token=token)

