from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from src.models.user import User, UserCreate, UserUpdate, Role, UserStatus

logger = logging.getLogger(__name__)


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def update_user(db: Session, user_id: int, update_data: UserUpdate) -> Optional[User]:
    user = db.get(User, user_id)
    if not user:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    if "password" in update_dict:
        update_dict["hashed_password"] = User.hash_password(update_dict.pop("password"))
    if "role" in update_dict and isinstance(update_dict["role"], str):
        update_dict["role"] = Role(update_dict["role"].lower())

    for key, value in update_dict.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    user = db.get(User, user_id)
    if not user:
        return None
    user.desactivar_usuario()
    db.commit()
    db.refresh(user)
    return user


def activate_user(db: Session, user_id: int) -> Optional[User]:
    user = db.get(User, user_id)
    if not user:
        return None
    user.estado = UserStatus.ACTIVO
    db.commit()
    db.refresh(user)
    return user
