from sqlalchemy import create_engine, text
from src.core.config import settings

def list_roles():
    # Crear conexión directa a la base de datos
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Listar los valores del enum 'role'
        result = conn.execute(text(
            """
            SELECT e.enumlabel 
            FROM pg_enum e 
            JOIN pg_type t ON e.enumtypid = t.oid 
            WHERE t.typname = 'role';
            """
        ))
        
        print("Roles definidos en la base de datos:")
        for row in result:
            print(f"- {row[0]}")

if __name__ == "__main__":
    list_roles()
