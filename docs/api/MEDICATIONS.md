# API de Gestión de Medicamentos

Esta documentación describe los endpoints disponibles para la gestión de medicamentos en el sistema.

## Tabla de Contenidos
- [Obtener Medicamentos](#obtener-medicamentos)
- [Obtener Medicamento por ID](#obtener-medicamento-por-id)
- [Crear Medicamento](#crear-medicamento)
- [Actualizar Medicamento](#actualizar-medicamento)
- [Eliminar Medicamento](#eliminar-medicamento)
- [Modelo de Datos](#modelo-de-datos)

---

## Obtener Medicamentos

Obtiene una lista de medicamentos con opciones de filtrado.

### URL
```
GET /api/v1/medications/
```

### Parámetros de Consulta
| Parámetro   | Tipo | Requerido | Descripción                              |
|-------------|------|-----------|------------------------------------------|
| skip        | int  | No        | Número de registros a saltar (paginación) |
| limit       | int  | No        | Número máximo de registros (máx. 100)    |
| name        | str  | No        | Filtrar por nombre (búsqueda parcial)     |
| category_id | int  | No        | Filtrar por ID de categoría              |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
{
  "status": "success",
  "total": 2,
  "skip": 0,
  "limit": 10,
  "count": 2,
  "data": [
    {
      "id": 1,
      "name": "Paracetamol 500mg",
      "description": "Analgésico y antipirético",
      "stock": 150,
      "min_stock": 10,
      "unit": "units",
      "category_id": 1,
      "intake_type_id": 1,
      "created_at": "2025-01-15T10:00:00",
      "updated_at": "2025-05-20T15:30:00"
    },
    {
      "id": 2,
      "name": "Ibuprofeno 400mg",
      "description": "Antiinflamatorio no esteroideo",
      "stock": 85,
      "min_stock": 10,
      "unit": "units",
      "category_id": 1,
      "intake_type_id": 2,
      "created_at": "2025-01-16T09:15:00",
      "updated_at": "2025-05-19T11:20:00"
    }
  ]
}
```

### Posibles Errores
- **400 Bad Request**: Parámetros de consulta inválidos
- **401 Unauthorized**: Token no proporcionado o inválido
- **404 Not Found**: No se encontró el recurso solicitado
- **422 Unprocessable Entity**: Error de validación en los datos de entrada
- **500 Internal Server Error**: Error interno del servidor

## Modelo de Datos

### Medicamento
| Campo          | Tipo    | Requerido | Descripción                                      |
|----------------|---------|-----------|--------------------------------------------------|
| id             | int     | Sí        | Identificador único del medicamento              |
| name           | string  | Sí        | Nombre del medicamento                          |
| description    | string  | No        | Descripción detallada                           |
| stock          | int     | Sí        | Cantidad actual en inventario                   |
| min_stock      | int     | Sí        | Nivel mínimo de inventario antes de alertar     |
| unit           | string  | Sí        | Unidad de medida (ej. mg, ml, unidades)         |
| category_id    | int     | No        | ID de la categoría a la que pertenece           |
| intake_type_id | int     | No        | ID del tipo de ingesta                          |
| created_at     | string  | No        | Fecha de creación (formato ISO 8601)            |
| updated_at     | string  | No        | Fecha de última actualización (formato ISO 8601)|

---

## Obtener Medicamento por ID

Obtiene los detalles de un medicamento específico por su ID.

### URL
```
GET /api/v1/medications/{medication_id}
```

### Parámetros de Ruta
| Parámetro    | Tipo | Requerido | Descripción         |
|--------------|------|-----------|---------------------|
| medication_id| int  | Sí        | ID del medicamento  |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "Paracetamol 500mg",
    "description": "Analgésico y antipirético",
    "stock": 150,
    "min_stock": 10,
    "unit": "units",
    "category_id": 1,
    "intake_type_id": 1,
    "created_at": "2025-01-15T10:00:00",
    "updated_at": "2025-05-20T15:30:00"
  }
  "created_at": "2025-01-15T10:00:00",
  "updated_at": "2025-05-20T15:30:00"
}
```

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **404 Not Found**: Medicamento no encontrado
- **500 Internal Server Error**: Error interno del servidor

---

## Crear Medicamento

Crea un nuevo medicamento en el sistema (solo administradores).

### URL
```
POST /api/v1/medications/
```

### Encabezados
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

### Cuerpo de la Solicitud
| Parámetro      | Tipo   | Requerido | Descripción                              |
|----------------|--------|-----------|------------------------------------------|
| name           | string | Sí        | Nombre del medicamento                   |
| description    | string | No        | Descripción del medicamento              |
| stock          | int    | No        | Cantidad en stock (por defecto: 0)       |
| category_id    | int    | No        | ID de la categoría del medicamento       |
| intake_type_id | int    | No        | ID del tipo de administración            |
| expiration_date| string | No        | Fecha de vencimiento (YYYY-MM-DD)        |
| price          | float  | No        | Precio unitario                          |

#### Ejemplo
```json
{
  "name": "Amoxicilina 500mg",
  "description": "Antibiótico de amplio espectro",
  "stock": 200,
  "category_id": 2,
  "intake_type_id": 3,
  "expiration_date": "2026-03-31",
  "price": 1.20
}
```

### Respuesta Exitosa (201 Created)
```json
{
  "id": 3,
  "name": "Amoxicilina 500mg",
  "description": "Antibiótico de amplio espectro",
  "stock": 200,
  "category_id": 2,
  "intake_type_id": 3,
  "expiration_date": "2026-03-31",
  "price": 1.20,
  "created_at": "2025-05-20T16:45:00",
  "updated_at": "2025-05-20T16:45:00"
}
```

### Posibles Errores
- **400 Bad Request**: Datos de entrada inválidos
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario sin permisos de administrador
- **500 Internal Server Error**: Error interno del servidor

---

## Actualizar Medicamento

Actualiza un medicamento existente (solo administradores).

### URL
```
PUT /api/v1/medications/{medication_id}
```

### Parámetros de Ruta
| Parámetro    | Tipo | Requerido | Descripción         |
|--------------|------|-----------|---------------------|
| medication_id| int  | Sí        | ID del medicamento  |

### Encabezados
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

### Cuerpo de la Solicitud
Mismos campos que en la creación, pero todos son opcionales.

#### Ejemplo
```json
{
  "stock": 180,
  "price": 1.10
}
```

### Respuesta Exitosa (200 OK)
```json
{
  "id": 3,
  "name": "Amoxicilina 500mg",
  "description": "Antibiótico de amplio espectro",
  "stock": 180,
  "category_id": 2,
  "intake_type_id": 3,
  "expiration_date": "2026-03-31",
  "price": 1.10,
  "created_at": "2025-05-20T16:45:00",
  "updated_at": "2025-05-20T17:30:00"
}
```

### Posibles Errores
- **400 Bad Request**: Datos de entrada inválidos
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario sin permisos de administrador
- **404 Not Found**: Medicamento no encontrado
- **500 Internal Server Error**: Error interno del servidor

---

## Eliminar Medicamento

Elimina un medicamento del sistema (solo administradores).

### URL
```
DELETE /api/v1/medications/{medication_id}
```

### Parámetros de Ruta
| Parámetro    | Tipo | Requerido | Descripción         |
|--------------|------|-----------|---------------------|
| medication_id| int  | Sí        | ID del medicamento  |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (204 No Content)
```
// Sin contenido en la respuesta
```

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario sin permisos de administrador
- **404 Not Found**: Medicamento no encontrado
- **500 Internal Server Error**: Error interno del servidor

---

## Notas de Seguridad

- Se requiere autenticación para todos los endpoints
- Solo los administradores pueden crear, actualizar o eliminar medicamentos
- Los usuarios regulares solo pueden ver la lista de medicamentos y los detalles de cada uno
