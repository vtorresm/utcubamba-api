from src.core.security import get_password_hash
from datetime import datetime

# Datos del usuario
password = "admin123"  # Cambia esto por la contraseña que desees
hashed_password = get_password_hash(password)

# Generar el SQL insert
sql = f"""
INSERT INTO users (name, email, hashed_password, role, is_active, created_at)
VALUES (
    'Admin User',
    'admin@example.com',
    '{hashed_password}',
    'admin',
    true,
    '{datetime.utcnow()}'
);
"""

print("=== SQL para insertar usuario ===")
print(sql)
