# API de Gestión de Usuarios

Esta documentación describe los endpoints disponibles para la gestión de usuarios en el sistema.

## Tabla de Contenidos
- [Obtener Usuarios](#obtener-usuarios)
- [Obtener Usuario Actual](#obtener-usuario-actual)
- [Obtener Usuario por ID](#obtener-usuario-por-id)
- [Actualizar Usuario Actual](#actualizar-usuario-actual)
- [Actualizar Usuario por ID (Admin)](#actualizar-usuario-por-id-admin)

---

## Obtener Usuarios

Obtiene una lista de todos los usuarios registrados en el sistema (solo administradores).

### URL
```
GET /api/v1/users/
```

### Parámetros de Consulta
| Parámetro | Tipo   | Requerido | Descripción                |
|-----------|--------|-----------|----------------------------|
| skip      | int    | No        | Número de registros a saltar (paginación) |
| limit     | int    | No        | Número máximo de registros a devolver (máx. 100) |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
[
  {
    "id": 1,
    "email": "admin@utcubamba.edu.pe",
    "role": "admin",
    "nombre": "Administrador",
    "cargo": "Administrador del Sistema",
    "departamento": "TI",
    "estado": "activo"
  },
  {
    "id": 2,
    "email": "usuario@utcubamba.edu.pe",
    "role": "user",
    "nombre": "Usuario Prueba",
    "cargo": "Docente",
    "departamento": "Académico",
    "estado": "activo"
  }
]
```

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario sin permisos de administrador
- **500 Internal Server Error**: Error interno del servidor

---

## Obtener Usuario Actual

Obtiene la información del usuario autenticado actualmente.

### URL
```
GET /api/v1/users/me
```

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
{
  "id": 2,
  "email": "usuario@utcubamba.edu.pe",
  "role": "user",
  "nombre": "Usuario Prueba",
  "cargo": "Docente",
  "departamento": "Académico",
  "contacto": "+51987654321",
  "estado": "activo",
  "fecha_ingreso": "2025-01-15",
  "fecha_creacion": "2025-01-15T10:00:00"
}
```

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **500 Internal Server Error**: Error interno del servidor

---

## Obtener Usuario por ID

Obtiene la información de un usuario específico por su ID (solo administradores).

### URL
```
GET /api/v1/users/{user_id}
```

### Parámetros de Ruta
| Parámetro | Tipo | Requerido | Descripción         |
|-----------|------|-----------|---------------------|
| user_id   | int  | Sí        | ID del usuario a consultar |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
{
  "id": 2,
  "email": "usuario@utcubamba.edu.pe",
  "role": "user",
  "nombre": "Usuario Prueba",
  "cargo": "Docente",
  "departamento": "Académico",
  "estado": "activo"
}
```

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario sin permisos de administrador
- **404 Not Found**: Usuario no encontrado
- **500 Internal Server Error**: Error interno del servidor

---

## Actualizar Usuario Actual

Actualiza la información del usuario autenticado actualmente. Los usuarios no administradores solo pueden actualizar ciertos campos.

### URL
```
PUT /api/v1/users/me
```

### Encabezados
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

### Cuerpo de la Solicitud
| Parámetro  | Tipo   | Requerido | Descripción                |
|------------|--------|-----------|----------------------------|
| nombre     | string | No        | Nuevo nombre completo      |
| cargo      | string | No        | Nuevo cargo                |
| departamento| string| No        | Nuevo departamento        |
| contacto   | string | No        | Nuevo número de contacto (único) |

#### Campos para administradores (adicionales):
| Parámetro  | Tipo   | Requerido | Descripción                |
|------------|--------|-----------|----------------------------|
| email      | string | No        | Nuevo correo electrónico   |
| role       | string | No        | Nuevo rol                 |

#### Ejemplo
```json
{
  "nombre": "Juan Pérez",
  "cargo": "Docente Titular",
  "departamento": "Ciencias",
  "contacto": "+51999999999"
}
```

### Respuesta Exitosa (200 OK)
```json
{
  "id": 2,
  "email": "usuario@utcubamba.edu.pe",
  "role": "user",
  "nombre": "Juan Pérez",
  "cargo": "Docente Titular",
  "departamento": "Ciencias",
  "contacto": "+51999999999",
  "estado": "activo"
}
```

### Posibles Errores
- **400 Bad Request**: 
  - Datos de entrada inválidos
  - El teléfono ya está registrado con otro usuario
  - No se proporcionaron campos válidos para actualizar
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Intento de modificar campos restringidos sin permisos
- **500 Internal Server Error**: Error interno del servidor

---

## Actualizar Usuario por ID (Admin)

Permite a un administrador actualizar cualquier usuario del sistema.

### URL
```
PUT /api/v1/users/admin/{user_id}
```

### Parámetros de Ruta
| Parámetro | Tipo | Requerido | Descripción         |
|-----------|------|-----------|---------------------|
| user_id   | int  | Sí        | ID del usuario a actualizar |

### Encabezados
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

### Cuerpo de la Solicitud
| Parámetro  | Tipo   | Requerido | Descripción                |
|------------|--------|-----------|----------------------------|
| email      | string | No        | Nuevo correo electrónico   |
| nombre     | string | No        | Nuevo nombre completo       |
| contacto   | string | No        | Nuevo número de contacto   |
| cargo      | string | No        | Nuevo cargo                |
| departamento| string| No        | Nuevo departamento        |
| role       | string | No        | Nuevo rol (solo admin)     |

#### Ejemplo
```json
{
  "nombre": "Nuevo Nombre",
  "cargo": "Nuevo Cargo",
  "departamento": "Nuevo Departamento",
  "contacto": "+51999999999",
  "role": "admin"
}
```

### Respuesta Exitosa (200 OK)
```json
{
  "id": 2,
  "email": "usuario@utcubamba.edu.pe",
  "role": "admin",
  "nombre": "Nuevo Nombre",
  "cargo": "Nuevo Cargo",
  "departamento": "Nuevo Departamento",
  "contacto": "+51999999999",
  "estado": "activo"
}
```

### Posibles Errores
- **400 Bad Request**: Datos de entrada inválidos o teléfono ya en uso
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario sin permisos de administrador
- **404 Not Found**: Usuario no encontrado
- **500 Internal Server Error**: Error interno del servidor

---

## Notas de Seguridad

- Solo los administradores pueden ver la lista completa de usuarios
- Los usuarios solo pueden modificar su propia información, excepto su rol
- El campo de teléfono debe ser único en todo el sistema
- Los usuarios no administradores no pueden modificar su correo electrónico
- Los campos sensibles como contraseñas nunca se devuelven en las respuestas
- Se requiere autenticación para todos los endpoints
