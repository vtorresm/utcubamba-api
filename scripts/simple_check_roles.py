import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

def check_roles():
    # Configuración de la conexión (ajusta según tu configuración)
    conn_params = {
        "dbname": "utcubamba",
        "user": "postgres",
        "password": "postgres",
        "host": "localhost",
        "port": "5432"
    }
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Verificar si el tipo de enum 'role' existe
        cursor.execute("""
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            LEFT JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typname = 'role';
        """)
        
        print("\n1. Valores del enum 'role':")
        roles = cursor.fetchall()
        if not roles:
            print("No se encontró el tipo de enum 'role'")
        else:
            for row in roles:
                print(f"- {row['enumlabel']}")
        
        # 2. Verificar la estructura de la tabla users
        cursor.execute("""
            SELECT column_name, data_type, udt_name, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users';
        """)
        
        print("\n2. Estructura de la tabla 'users':")
        for row in cursor.fetchall():
            print(f"- {row['column_name']}: {row['data_type']} ({row['udt_name']}), Nullable: {row['is_nullable']}")
        
        # 3. Verificar los usuarios existentes
        cursor.execute("""
            SELECT id, email, role, estado FROM users;
        """)
        
        print("\n3. Usuarios existentes:")
        for row in cursor.fetchall():
            print(f"- ID: {row['id']}, Email: {row['email']}, Rol: {row['role']}, Estado: {row['estado']}")
        
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_roles()
