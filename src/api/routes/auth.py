from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.core.security import verify_password, get_password_hash, create_access_token
from src.utils.token_utils import create_refresh_token, validate_refresh_token
from src.db.database import get_db
from src.models.schemas import Token, User, UserCreate, RefreshTokenRequest
from src.models.database_models import User as UserModel, RefreshToken
from src.api.dependencies import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=User)
def register(user: UserCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Attempting to register user with email: {user.email}")
    if user.role != "user" and current_user.role != "admin":
        logger.warning(f"Non-admin user {current_user.email} attempted to assign role: {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign roles"
        )
    db_user = UserModel(
        name=user.name,
        email=user.email,
        password=get_password_hash(user.password),
        role=user.role
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"User registered successfully: {user.email}")
        return db_user
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to register user: Email {user.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Login attempt for user: {form_data.username}")
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(user.id, db)
    logger.info(f"Login successful for user: {form_data.username}")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    logger.info("Attempting to refresh token")
    user = validate_refresh_token(refresh_request.refresh_token, db)
    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_request.refresh_token).first()
    if db_token:
        db.delete(db_token)
        db.commit()
        logger.debug(f"Deleted old refresh token for user ID: {user['id']}")
    access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    refresh_token = create_refresh_token(user["id"], db)
    logger.info(f"Token refreshed successfully for user: {user['email']}")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/logout")
def logout(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    logger.info("Logout request received")
    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_request.refresh_token).first()
    if db_token:
        db.delete(db_token)
        db.commit()
        logger.info("Refresh token invalidated successfully")
    else:
        logger.warning("Attempted to logout with invalid or non-existent refresh token")
    return {"message": "Logged out successfully"}