-- Insertar un nuevo usuario
INSERT INTO users (
    name,
    email,
    hashed_password,
    role,
    is_active
) VALUES (
    'Juan Perez',
    'juan.perez@example.com',
    '$2b$12$NWcgHYt4jZ7AEG2wnjLqJOX8L.bNW6vMUNEnRF9abx/MdW7YlIu8S', -- Este es un hash de ejemplo, reemplazar con el hash real
    'user',
    true
) RETURNING *;

-- Verificar el usuario insertado
SELECT * FROM users WHERE email = 'juan.perez@example.com';
