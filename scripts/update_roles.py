import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Agregar el directorio raíz al path para poder importar src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de la base de datos (ajusta según tu configuración)
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/utcubamba"

def update_roles():
    # Crear conexión directa a la base de datos
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Verificar si el tipo de enum 'role' existe
        result = conn.execute(text(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'role'
            ) AS type_exists;
            """
        ))
        type_exists = result.scalar()
        
        if not type_exists:
            print("El tipo 'role' no existe en la base de datos.")
            return
            
        # Verificar si los roles ya existen
        result = conn.execute(text(
            """
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = 'role'::regtype
            ORDER BY enumsortorder;
            """
        ))
        
        existing_roles = [row[0] for row in result]
        print("Roles existentes en la base de datos:", ", ".join(existing_roles))
        
        # Roles que queremos agregar
        roles_to_add = ['farmacia', 'enfermeria']
        
        # Verificar y agregar roles faltantes
        added_roles = []
        for role in roles_to_add:
            if role not in existing_roles:
                try:
                    conn.execute(text(f"ALTER TYPE role ADD VALUE IF NOT EXISTS '{role}'"))
                    added_roles.append(role)
                except Exception as e:
                    print(f"Error al agregar el rol '{role}': {e}")
        
        if added_roles:
            conn.commit()
            print(f"Se agregaron los roles: {', '.join(added_roles)}")
        else:
            print("No se agregaron nuevos roles.")

if __name__ == "__main__":
    update_roles()
