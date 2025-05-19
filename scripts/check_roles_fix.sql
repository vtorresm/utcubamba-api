-- 1. Verificar si el tipo de enum 'role' existe
SELECT t.typname, e.enumlabel 
FROM pg_type t 
LEFT JOIN pg_enum e ON t.oid = e.enumtypid 
WHERE t.typname = 'role';

-- 2. Si el tipo 'role' no tiene los valores necesarios, podemos intentar agregarlos
-- Nota: No podemos eliminar valores de un enum existente, pero podemos crear uno nuevo
DO $$
BEGIN
    -- Verificar si el tipo 'role' existe
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role') THEN
        -- Verificar si los valores ya existen
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumtypid = 'role'::regtype 
            AND enumlabel = 'farmacia'
        ) THEN
            -- Crear un nuevo tipo temporal con los valores correctos
            CREATE TYPE role_new AS ENUM ('admin', 'user', 'farmacia', 'enfermeria');
            
            -- Actualizar la columna en la tabla users
            ALTER TABLE users 
            ALTER COLUMN role TYPE role_new 
            USING (role::text::role_new);
            
            -- Eliminar el tipo antiguo
            DROP TYPE role;
            
            -- Renombrar el nuevo tipo
            ALTER TYPE role_new RENAME TO role;
            
            RAISE NOTICE 'Se actualizó el tipo role con los valores correctos';
        ELSE
            RAISE NOTICE 'El tipo role ya contiene los valores correctos';
        END IF;
    ELSE
        RAISE NOTICE 'El tipo role no existe en la base de datos';
    END IF;
END $$;

-- 3. Verificar la estructura de la tabla users
SELECT column_name, data_type, udt_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users';

-- 4. Verificar los usuarios existentes
SELECT id, email, role, estado FROM users;
