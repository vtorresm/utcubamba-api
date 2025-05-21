from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from src.models.user import User, Role, UserStatus
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
                detail={"error": "invalid_credentials", "message": "Incorrect email or password"},
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
    def register_user(
        db: Session,
        email: str,
        password: str,
        nombre: str,
        cargo: str,
        departamento: str,
        contacto: Optional[str] = None,
        role: str = "user"
    ) -> User:
        """
        Registra un nuevo usuario con todos los campos requeridos.
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario (debe ser único)
            password: Contraseña en texto plano
            nombre: Nombre completo del usuario
            cargo: Cargo o puesto del usuario
            departamento: Departamento o área del usuario
            contacto: Número de contacto (opcional, debe ser único)
            role: Rol del usuario en el sistema
            
        Returns:
            User: El usuario creado
            
        Raises:
            HTTPException: Si el correo o teléfono ya están registrados o hay un error en los datos
        """
        # Verificar si el email ya existe
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "email_exists", "message": "El correo electrónico ya está registrado"}
            )
            
        # Verificar si el teléfono ya está registrado (solo si se proporciona)
        if contacto:
            existing_contact = db.query(User).filter(
                User.contacto == contacto,
                User.contacto.isnot(None)
            ).first()
            if existing_contact:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "contact_exists",
                        "message": "El número de teléfono ya está registrado con otro usuario"
                    }
                )

        try:
            # Si el rol es una cadena, convertirla al enum correspondiente
            if isinstance(role, str):
                role_enum = Role(role.lower())
            else:
                role_enum = role
                
            # Verificar si el rol es válido
            if role_enum not in list(Role):
                valid_roles = [r.value for r in Role]
                raise ValueError(f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}")
                
            # Crear el usuario con todos los campos requeridos
            hashed_password = User.hash_password(password)
            user = User(
                email=email.lower(),
                hashed_password=hashed_password,
                nombre=nombre,
                cargo=cargo,
                departamento=departamento,
                contacto=contacto,
                role=role_enum,  # Usar el enum convertido
                estado=UserStatus.ACTIVO
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        except ValueError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_role",
                    "message": str(e)
                }
            )
        except Exception as e:
            db.rollback()
            # Log del error para depuración
            import traceback
            print(f"Error al crear usuario: {str(e)}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "user_creation_failed",
                    "message": f"Error al crear el usuario: {str(e)}"
                }
            )

    @staticmethod
    async def generate_reset_token(db: Session, email: str) -> Optional[str]:
        """
        Genera un token para restablecer la contraseña de forma asíncrona.
        
        Args:
            db: Sesión de base de datos
            email: Correo electrónico del usuario
            
        Returns:
            str: Token generado o None si hay un error
        """
        from sqlalchemy.future import select
        from sqlalchemy import or_
        
        try:
            # Buscar usuario por email
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
                
            # Generar un token único
            token = str(uuid.uuid4())
            
            # Crear token de restablecimiento
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
            # Eliminar tokens anteriores del usuario
            await db.execute(
                PasswordResetToken.__table__.delete()
                .where(PasswordResetToken.user_id == user.id)
            )
            
            # Guardar nuevo token
            db.add(reset_token)
            await db.commit()
            
            return token
            
        except Exception as e:
            await db.rollback()
            import logging
            logging.error(f"Error al generar token de restablecimiento: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        """
        Restablece la contraseña usando un token.
        """
        reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_token", "message": "Invalid or expired token"}
            )

        if reset_token.expires_at < datetime.utcnow():
            db.delete(reset_token)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "token_expired", "message": "Token has expired"}
            )

        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Actualizar la contraseña
        user.hashed_password = User.hash_password(new_password)
        db.delete(reset_token)  # Eliminar el token usado
        db.commit()