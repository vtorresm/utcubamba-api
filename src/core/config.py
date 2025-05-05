from dotenv import load_dotenv
import os

load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "utcubamba_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_REFRESH_TOKENS = 5  # Límite máximo de refresh tokens por usuario
ALLOWED_ROLES = {"user", "admin"}  # Roles permitidos