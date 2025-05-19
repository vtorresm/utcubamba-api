from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from src.models.user import User, Role
from src.models.password_reset_token import PasswordResetToken
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
import uuid

# Cargar variables de entorno
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Configuración de OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class AuthService:
    @staticmethod
    def verify_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Verifica las credenciales del usuario.
        """
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un token JWT.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """
        Obtiene el usuario actual a partir del token JWT.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        return user

    @staticmethod
    def register_user(db: Session, email: str, password: str, role: str = Role.USER) -> User:
        """
        Registra un nuevo usuario.
        """
        # Verificar si el email ya existe
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Validar el rol
        if role not in [Role.ADMIN, Role.USER]:
            raise HTTPException(status_code=400, detail="Invalid role")

        # Crear el usuario
        hashed_password = User.hash_password(password)
        user = User(email=email, hashed_password=hashed_password, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def generate_reset_token(db: Session, email: str) -> str:
        """
        Genera un token para restablecer la contraseña.
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Generar un token único
        token = str(uuid.uuid4())
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(reset_token)
        db.commit()
        return token

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        """
        Restablece la contraseña usando un token.
        """
        reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
        if not reset_token:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        if reset_token.expires_at < datetime.utcnow():
            db.delete(reset_token)
            db.commit()
            raise HTTPException(status_code=400, detail="Token has expired")

        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Actualizar la contraseña
        user.hashed_password = User.hash_password(new_password)
        db.delete(reset_token)  # Eliminar el token usado
        db.commit()