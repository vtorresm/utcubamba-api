import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verify_medications_structure():
    try:
        # Establecer conexión
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "utcubamba_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "root"),
            port=os.getenv("DB_PORT", "5432")
        )
        
        # Crear un cursor
        cur = conn.cursor()
        
        # 1. Obtener información de la tabla
        print("\n" + "="*80)
        print("INFORMACIÓN DE LA TABLA 'medications'")
        print("="*80)
        
        # Obtener columnas
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default, 
                   character_maximum_length, numeric_precision, datetime_precision
            FROM information_schema.columns 
            WHERE table_name = 'medications'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        
        print("\nCOLUMNAS:")
        print("-" * 40)
        for col in columns:
            print(f"- {col[0]} ({col[1]})")
            print(f"  Nulable: {'Sí' if col[2] == 'YES' else 'No'}")
            if col[3]:
                print(f"  Valor por defecto: {col[3]}")
            if col[4]:
                print(f"  Longitud máxima: {col[4]}")
            if col[5]:
                print(f"  Precisión numérica: {col[5]}")
            if col[6]:
                print(f"  Precisión fecha/hora: {col[6]}")
        
        # Verificar restricciones
        cur.execute("""
            SELECT tc.constraint_name, tc.constraint_type, 
                   ccu.column_name, tc.is_deferrable, tc.initially_deferred
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_name = 'medications';
        """)
        
        constraints = cur.fetchall()
        
        print("\nRESTRICCIONES:")
        print("-" * 40)
        if constraints:
            for constr in constraints:
                print(f"- Nombre: {constr[0]}")
                print(f"  Tipo: {constr[1]}")
                if constr[2]:
                    print(f"  Columna: {constr[2]}")
                print(f"  Diferible: {constr[3]}")
                print(f"  Inicialmente diferida: {constr[4]}")
        else:
            print("No se encontraron restricciones.")
        
        # Verificar comentarios
        cur.execute("""
            SELECT cols.column_name, pg_catalog.col_description(format('%s.%s', cols.table_schema, cols.table_name)::regclass::oid, cols.ordinal_position) as column_comment
            FROM information_schema.columns cols
            WHERE cols.table_name = 'medications';
        """)
        
        comments = cur.fetchall()
        
        print("\nCOMENTARIOS DE COLUMNAS:")
        print("-" * 40)
        for comment in comments:
            if comment[1]:
                print(f"- {comment[0]}: {comment[1]}")
        
        # Cerrar cursor y conexión
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        print("Asegúrate de que:")
        print("1. PostgreSQL está en ejecución")
        print("2. Las credenciales de la base de datos son correctas")
        print("3. La base de datos y el usuario existen")
        print(f"Error detallado: {str(e)}")

if __name__ == "__main__":
    print("Verificando estructura de la tabla 'medications'...")
    verify_medications_structure()
