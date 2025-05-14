from src.core.security import get_password_hash

# Generar hash para una contraseña
password = "12345678"
hashed_password = get_password_hash(password)

print(f"Hash generado: {hashed_password}")
