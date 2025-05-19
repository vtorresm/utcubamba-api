from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

def check_roles():
    # Crear conexión directa a la base de datos
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Verificar los roles existentes
        result = conn.execute(text(
            """
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typname = 'role';
            """
        ))
        
        print("Roles existentes en la base de datos:")
        for row in result:
            print(f"- {row[1]}")
        
        # Verificar si los roles FARMACIA y ENFERMERIA existen
        result = conn.execute(text(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumtypid = 'role'::regtype 
                AND enumlabel = 'farmacia'
            ) AS exists_farmacia,
            EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumtypid = 'role'::regtype 
                AND enumlabel = 'enfermeria'
            ) AS exists_enfermeria;
            """
        ))
        
        exists_farmacia, exists_enfermeria = result.fetchone()
        
        if not exists_farmacia or not exists_enfermeria:
            print("\nAgregando roles faltantes...")
            if not exists_farmacia:
                conn.execute(text("ALTER TYPE role ADD VALUE IF NOT EXISTS 'farmacia'"))
                print("- Se agregó el rol 'farmacia'")
            if not exists_enfermeria:
                conn.execute(text("ALTER TYPE role ADD VALUE IF NOT EXISTS 'enfermeria'"))
                print("- Se agregó el rol 'enfermeria'")
            
            # Confirmar los cambios
            conn.commit()
            print("\nRoles actualizados correctamente.")
        else:
            print("\nTodos los roles ya existen en la base de datos.")

if __name__ == "__main__":
    check_roles()
