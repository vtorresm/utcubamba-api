-- Verificar si el tipo de enum 'role' existe
SELECT t.typname, e.enumlabel 
FROM pg_type t 
LEFT JOIN pg_enum e ON t.oid = e.enumtypid 
WHERE t.typname = 'role';

-- Verificar la estructura de la tabla users
SELECT column_name, data_type, udt_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users';

-- Verificar los usuarios existentes
SELECT id, email, role, estado FROM users;
