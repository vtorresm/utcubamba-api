import uuid
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.models.database_models import RefreshToken, User
from src.core.config import REFRESH_TOKEN_EXPIRE_DAYS, MAX_REFRESH_TOKENS
import logging

logger = logging.getLogger(__name__)

def create_refresh_token(user_id: int, db: Session = Depends(get_db)):
    logger.debug(f"Creating refresh token for user ID: {user_id}")
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Verificar número de refresh tokens activos
    token_count = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.expires_at > datetime.utcnow()
    ).count()
    logger.debug(f"User ID: {user_id} has {token_count} active refresh tokens")
    
    if token_count >= MAX_REFRESH_TOKENS:
        # Eliminar los tokens más antiguos
        oldest_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at > datetime.utcnow()
        ).order_by(RefreshToken.created_at.asc()).limit(token_count - MAX_REFRESH_TOKENS + 1).all()
        for old_token in oldest_tokens:
            db.delete(old_token)
            logger.debug(f"Deleted old refresh token ID: {old_token.id} for user ID: {user_id}")
    
    # Crear nuevo refresh token
    new_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(new_token)
    db.commit()
    logger.info(f"Created new refresh token for user ID: {user_id}")
    return token

def validate_refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    logger.debug(f"Validating refresh token")
    token_data = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not token_data:
        logger.warning("Invalid refresh token provided")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if token_data.expires_at < datetime.utcnow():
        logger.warning(f"Expired refresh token for user ID: {token_data.user_id}")
        raise HTTPException(status_code=401, detail="Refresh token expired")
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        logger.error(f"User ID: {token_data.user_id} not found for refresh token")
        raise HTTPException(status_code=401, detail="User not found")
    logger.debug(f"Refresh token validated for user: {user.email}")
    return {"email": user.email, "role": user.role, "id": user.id}