# API de Autenticación

Esta documentación describe los endpoints disponibles para la autenticación de usuarios en el sistema.

## Tabla de Contenidos
- [Registro de Usuario](#registro-de-usuario)
- [Inicio de Sesión](#inicio-de-sesión)
- [Solicitud de Restablecimiento de Contraseña](#solicitud-de-restablecimiento-de-contraseña)
- [Confirmación de Restablecimiento de Contraseña](#confirmación-de-restablecimiento-de-contraseña)

---

## Registro de Usuario

Crea una nueva cuenta de usuario en el sistema.

### URL
```
POST /api/v1/auth/register
```

### Cuerpo de la Solicitud

| Parámetro    | Tipo   | Requerido | Descripción                                       |
|--------------|--------|-----------|---------------------------------------------------|
| nombre       | string | Sí        | Nombre completo del usuario (2-100 caracteres)    |
| email        | string | Sí        | Correo electrónico institucional                   |
| password     | string | Sí        | Contraseña (mínimo 6 caracteres)                  |
| cargo        | string | Sí        | Puesto o cargo del usuario (2-100 caracteres)     |
| departamento | string | Sí        | Área o departamento (2-100 caracteres)            |
| contacto     | string | No        | Número de teléfono o extensión (8-50 caracteres)  |
| role         | string | No        | Rol del usuario (user, admin, farmacia, enfermeria) |

#### Ejemplo
```json
{
  "nombre": "Juan Pérez",
  "email": "juan.perez@utcubamba.edu.pe",
  "password": "miclave123",
  "cargo": "Docente de Matemáticas",
  "departamento": "Académico",
  "contacto": "+51987654321",
  "role": "user"
}
```

### Respuesta Exitosa (201 Created)
```json
{
  "message": "Usuario registrado exitosamente",
  "data": {
    "id": 1,
    "nombre": "Juan Pérez",
    "email": "juan.perez@utcubamba.edu.pe",
    "cargo": "Docente de Matemáticas",
    "departamento": "Académico",
    "contacto": "+51987654321",
    "role": "user",
    "estado": "activo",
    "fecha_ingreso": "2025-05-20T22:06:00",
    "fecha_creacion": "2025-05-20T22:06:00"
  }
}
```

### Posibles Errores
- **400 Bad Request**: Datos de entrada inválidos o correo ya registrado
- **422 Unprocessable Entity**: Error de validación en los datos
- **500 Internal Server Error**: Error interno del servidor

---

## Inicio de Sesión

Autentica a un usuario y devuelve un token JWT.

### URL
```
POST /api/v1/auth/login
```

### Cuerpo de la Solicitud

| Parámetro | Tipo   | Requerido | Descripción                  |
|-----------|--------|-----------|------------------------------|
| username  | string | Sí        | Correo electrónico del usuario |
| password  | string | Sí        | Contraseña del usuario        |

#### Ejemplo
```json
{
  "username": "juan.perez@utcubamba.edu.pe",
  "password": "miclave123"
}
```

### Respuesta Exitosa (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "juan.perez@utcubamba.edu.pe",
    "role": "user",
    "status": "activo"
  }
}
```

### Posibles Errores
- **401 Unauthorized**: Credenciales inválidas
- **422 Unprocessable Entity**: Error de validación
- **500 Internal Server Error**: Error interno del servidor

---

## Solicitud de Restablecimiento de Contraseña

Envía un correo con un enlace para restablecer la contraseña.

### URL
```
POST /api/v1/auth/password-reset
```

### Cuerpo de la Solicitud

| Parámetro | Tipo   | Requerido | Descripción                  |
|-----------|--------|-----------|------------------------------|
| email     | string | Sí        | Correo electrónico del usuario |

#### Ejemplo
```json
{
  "email": "juan.perez@utcubamba.edu.pe"
}
```

### Respuesta Exitosa (200 OK)
```json
{
  "message": "Si su correo está registrado, recibirá un enlace para restablecer su contraseña"
}
```

### Notas
- Por razones de seguridad, la respuesta es la misma independientemente de si el correo existe o no.
- En un entorno de producción, se enviaría un correo con un token de restablecimiento.

---

## Confirmación de Restablecimiento de Contraseña

Establece una nueva contraseña usando un token de restablecimiento.

### URL
```
POST /api/v1/auth/password-reset/confirm
```

### Cuerpo de la Solicitud

| Parámetro   | Tipo   | Requerido | Descripción                           |
|-------------|--------|-----------|---------------------------------------|
| token       | string | Sí        | Token de restablecimiento             |
| new_password| string | Sí        | Nueva contraseña (mínimo 6 caracteres) |

#### Ejemplo
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "nuevacontraseña123"
}
```

### Respuesta Exitosa (200 OK)
```json
{
  "message": "Contraseña restablecida exitosamente"
}
```

### Posibles Errores
- **400 Bad Request**: Token inválido o expirado
- **422 Unprocessable Entity**: Error de validación
- **500 Internal Server Error**: Error interno del servidor

---

## Uso del Token JWT

Después de iniciar sesión, incluye el token JWT en el encabezado de autorización de las solicitudes subsiguientes:

```
Authorization: Bearer <token_jwt>
```

El token JWT tiene una duración limitada y debe renovarse mediante un nuevo inicio de sesión cuando expire.
