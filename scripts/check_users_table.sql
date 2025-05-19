-- Verificar la estructura de la tabla users
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users';

-- Verificar los valores del enum 'role'
SELECT t.typname, e.enumlabel 
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid 
WHERE t.typname = 'role';

-- Verificar los usuarios existentes
SELECT id, email, role, estado FROM users;
