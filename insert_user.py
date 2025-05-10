from src.db.database import get_db
from src.models.database_models import User
from datetime import datetime

# Crear una sesión
with get_db() as db:
    # Crear el usuario
    user = User(
        name="Admin User",
        email="admin@example.com",
        hashed_password="$2b$12$aMcknWotGvWf0u5xnK4BB.MwXdkCr5VN21WXLAS5I6qkHZXGulc/e",
        role="admin",
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    # Agregar y guardar en la base de datos
    db.add(user)
    db.commit()
    print("Usuario creado exitosamente")
