from src.core.database import engine, create_db_and_tables, SQLALCHEMY_DATABASE_URL
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def reset_database():
    """Elimina y vuelve a crear la base de datos."""
    # Obtener la URL de la base de datos
    db_url = SQLALCHEMY_DATABASE_URL
    
    # Crear una URL para la base de datos 'postgres' predeterminada
    from urllib.parse import urlparse, urlunparse
    parsed_url = urlparse(db_url)
    postgres_db_url = urlunparse(parsed_url._replace(path='/postgres'))
    
    safe_db_url = f"{parsed_url.scheme}://{parsed_url.username}:***@{parsed_url.hostname}:{parsed_url.port}{parsed_url.path}"
    
    print(f"Reiniciando base de datos: {safe_db_url}")
    
    try:
        # Conectarse a la base de datos 'postgres' predeterminada
        postgres_engine = create_engine(postgres_db_url)
        
        with postgres_engine.connect() as conn:
            # Terminar todas las conexiones a la base de datos objetivo
            conn.execute(text("COMMIT"))  # Terminar cualquier transacción pendiente
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = :database
                AND pid <> pg_backend_pid();
            """), {"database": parsed_url.path[1:]})  # Eliminar la barra inicial
            
            # Eliminar la base de datos si existe
            conn.execute(text("COMMIT"))  # Necesario para ejecutar DDL después de DML
            conn.execute(text(f'DROP DATABASE IF EXISTS "{parsed_url.path[1:]}"'))
            
            # Crear una nueva base de datos
            conn.execute(text("COMMIT"))  # Asegurarse de que no hay transacciones pendientes
            conn.execute(text(f'CREATE DATABASE "{parsed_url.path[1:]}"'))
            
    except Exception as e:
        print(f"Error al reiniciar la base de datos: {e}")
        return
    finally:
        # Asegurarse de cerrar la conexión
        postgres_engine.dispose()
    
    # Crear todas las tablas
    print("Creando tablas...")
    create_db_and_tables()
    
    print("Base de datos reiniciada exitosamente.")

if __name__ == "__main__":
    confirm = input("¿Estás seguro de que deseas eliminar y recrear la base de datos? (s/n): ")
    if confirm.lower() == 's':
        reset_database()
    else:
        print("Operación cancelada.")
