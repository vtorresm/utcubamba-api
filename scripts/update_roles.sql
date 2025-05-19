-- Verificar roles existentes
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = 'role'::regtype
ORDER BY enumsortorder;

-- Agregar roles faltantes si no existen
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumtypid = 'role'::regtype 
        AND enumlabel = 'farmacia'
    ) THEN
        ALTER TYPE role ADD VALUE 'farmacia';
        RAISE NOTICE 'Se agregó el rol farmacia';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumtypid = 'role'::regtype 
        AND enumlabel = 'enfermeria'
    ) THEN
        ALTER TYPE role ADD VALUE 'enfermeria';
        RAISE NOTICE 'Se agregó el rol enfermeria';
    END IF;
END $$;

-- Verificar los roles actualizados
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = 'role'::regtype
ORDER BY enumsortorder;
