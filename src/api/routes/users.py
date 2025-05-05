from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime
from src.core.security import get_password_hash, verify_password
from src.db.database import get_db
from src.models.schemas import User, UserCreate, RefreshTokenInfo
from src.models.database_models import User as UserModel, RefreshToken
from src.api.dependencies import get_current_user, require_role
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=User)
def create_user(user: UserCreate, current_user: UserModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to create user with email: {user.email}")
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
        logger.info(f"User created successfully: {user.email}")
        return db_user
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to create user: Email {user.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, current_user: UserModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Listing users (skip={skip}, limit={limit}) by admin: {current_user.email}")
    users = db.query(UserModel).offset(skip).limit(limit).all()
    logger.debug(f"Retrieved {len(users)} users")
    return users

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Fetching user ID: {user_id} by user: {current_user.email}")
    if current_user.role != "admin" and current_user.id != user_id:
        logger.warning(f"User {current_user.email} attempted unauthorized access to user ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        logger.error(f"User ID: {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    logger.debug(f"User retrieved: {user.email}")
    return user

@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Attempting to update user ID: {user_id} by user: {current_user.email}")
    if current_user.role != "admin" and current_user.id != user_id:
        logger.warning(f"User {current_user.email} attempted unauthorized update of user ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    if user.role != "user" and current_user.role != "admin":
        logger.warning(f"Non-admin user {current_user.email} attempted to assign role: {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign roles"
        )
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        logger.error(f"User ID: {user_id} not found for update")
        raise HTTPException(status_code=404, detail="User not found")
    
    password_changed = not verify_password(user.password, db_user.password)
    
    db_user.name = user.name
    db_user.email = user.email
    db_user.password = get_password_hash(user.password)
    db_user.role = user.role
    
    if password_changed:
        logger.info(f"Password changed for user ID: {user_id}, revoking refresh tokens")
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at > datetime.utcnow()
        ).delete()
    
    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"User updated successfully: {db_user.email}")
        return db_user
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to update user: Email {user.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

@router.delete("/{user_id}")
def delete_user(user_id: int, current_user: UserModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to delete user ID: {user_id} by admin: {current_user.email}")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        logger.error(f"User ID: {user_id} not found for deletion")
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    logger.info(f"User deleted successfully: {user.email}")
    return {"message": "User deleted successfully"}

@router.post("/me/revoke-refresh-tokens")
def revoke_own_refresh_tokens(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"User {current_user.email} requested to revoke their refresh tokens")
    deleted_count = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.expires_at > datetime.utcnow()
    ).delete()
    db.commit()
    logger.info(f"Revoked {deleted_count} refresh tokens for user: {current_user.email}")
    return {"message": "All your refresh tokens revoked successfully"}

@router.get("/{user_id}/refresh-tokens", response_model=List[RefreshTokenInfo])
def get_user_refresh_tokens(user_id: int, current_user: UserModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Admin {current_user.email} fetching refresh tokens for user ID: {user_id}")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        logger.error(f"User ID: {user_id} not found for refresh token retrieval")
        raise HTTPException(status_code=404, detail="User not found")
    tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.expires_at > datetime.utcnow()
    ).order_by(RefreshToken.created_at.desc()).all()
    logger.debug(f"Retrieved {len(tokens)} active refresh tokens for user ID: {user_id}")
    return tokens

@router.post("/{user_id}/revoke-refresh-tokens")
def revoke_user_refresh_tokens(user_id: int, current_user: UserModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Admin {current_user.email} requested to revoke refresh tokens for user ID: {user_id}")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        logger.error(f"User ID: {user_id} not found for refresh token revocation")
        raise HTTPException(status_code=404, detail="User not found")
    deleted_count = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.expires_at > datetime.utcnow()
    ).delete()
    db.commit()
    logger.info(f"Revoked {deleted_count} refresh tokens for user ID: {user_id}")
    return {"message": f"All refresh tokens for user {user_id} revoked successfully"}