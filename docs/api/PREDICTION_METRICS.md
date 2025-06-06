# API de Métricas de Predicción

Esta documentación describe los endpoints disponibles para gestionar las métricas de los modelos de predicción.

## Tabla de Contenidos
- [Obtener Todas las Métricas](#obtener-todas-las-métricas)
- [Obtener Métrica por ID](#obtener-métrica-por-id)
- [Crear Nueva Métrica](#crear-nueva-métrica)
- [Obtener Métricas por Medicamento](#obtener-métricas-por-medicamento)
- [Obtener Últimas Métricas de un Medicamento](#obtener-últimas-métricas-de-un-medicamento)

---

## Obtener Todas las Métricas

Obtiene todas las métricas de los modelos de predicción con filtros opcionales.

### URL
```
GET /api/v1/prediction-metrics/
```

### Parámetros de Consulta
| Parámetro     | Tipo   | Requerido | Descripción                                     |
|---------------|--------|-----------|------------------------------------------------|
| medication_id | int    | No        | Filtrar por ID de medicamento                  |
| days          | int    | No        | Filtrar por los últimos N días                 |
| limit         | int    | No        | Límite de resultados (por defecto: 100)        |
| offset        | int    | No        | Desplazamiento para paginación (por defecto: 0)|

### Encabezados
```
Authorization: Bearer <token_jwt>
Accept: application/json
```

### Respuesta Exitosa (200 OK)
```json
[
  {
    "id": 1,
    "model_version": "v1.2.3",
    "accuracy": 0.92,
    "mae": 1.5,
    "mse": 3.2,
    "r2_score": 0.89,
    "trained_at": "2025-06-05T15:30:00.000000",
    "training_duration": 120.5,
    "features_used": ["sales_history", "seasonality", "price", "stock_level"],
    "parameters": {
      "learning_rate": 0.001,
      "epochs": 100,
      "batch_size": 32
    },
    "medication_id": 1
  }
]
```

### Campos de Respuesta
| Campo             | Tipo    | Descripción                                      |
|-------------------|---------|--------------------------------------------------|
| id                | int     | ID único de la métrica                          |
| created_at        | string  | Fecha y hora de creación                        |
| updated_at        | string  | Fecha y hora de última actualización            |
| model_version     | string  | Versión del modelo                              |
| accuracy          | float   | Precisión del modelo (0 a 1)                   |
| mae               | float   | Error absoluto medio                            |
| mse               | float   | Error cuadrático medio                          |
| r2_score          | float   | Coeficiente de determinación R²                 |
| trained_at        | string  | Fecha y hora del entrenamiento                  |
| training_duration | float   | Duración del entrenamiento en segundos          |
| features_used     | array   | Lista de características utilizadas              |
| parameters        | object  | Parámetros del modelo                           |
| medication_id     | int     | ID del medicamento asociado (opcional)          |

---

## Obtener Métrica por ID

Obtiene los detalles de una métrica específica por su ID.

### URL
```
GET /api/v1/prediction-metrics/{metric_id}
```

### Parámetros de Ruta
| Parámetro | Tipo | Descripción                |
|-----------|------|----------------------------|
| metric_id | int  | ID de la métrica a consultar |

### Encabezados
```
Authorization: Bearer <token_jwt>
Accept: application/json
```

### Respuesta Exitosa (200 OK)
```json
{
  "id": 1,
  "model_version": "v1.2.3",
  "accuracy": 0.92,
  "mae": 1.5,
  "mse": 3.2,
  "r2_score": 0.89,
  "trained_at": "2025-06-05T15:30:00.000000",
  "training_duration": 120.5,
  "features_used": ["sales_history", "seasonality", "price", "stock_level"],
  "parameters": {
    "learning_rate": 0.001,
    "epochs": 100,
    "batch_size": 32
  },
  "medication_id": 1
}
```

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario no tiene permisos suficientes
- **404 Not Found**: Métrica no encontrada

---

## Crear Nueva Métrica

Crea una nueva entrada de métricas para un modelo de predicción.

### URL
```
POST /api/v1/prediction-metrics/
```

### Cuerpo de la Solicitud
```json
{
  "model_version": "v1.2.4",
  "accuracy": 0.94,
  "mae": 1.2,
  "mse": 2.8,
  "r2_score": 0.91,
  "training_duration": 135.2,
  "features_used": ["sales_history", "seasonality", "price", "stock_level", "promotions"],
  "parameters": {
    "learning_rate": 0.001,
    "epochs": 120,
    "batch_size": 32,
    "layers": [64, 32, 16]
  },
  "medication_id": 1
}
```

### Campos Requeridos
| Campo             | Tipo    | Descripción                                      |
|-------------------|---------|--------------------------------------------------|
| model_version     | string  | Versión del modelo                              |
| accuracy          | float   | Precisión del modelo (0 a 1)                   |
| mae               | float   | Error absoluto medio                            |
| mse               | float   | Error cuadrático medio                          |
| r2_score          | float   | Coeficiente de determinación R²                 |
| training_duration | float   | Duración del entrenamiento en segundos          |
| features_used     | array   | Lista de características utilizadas              |
| parameters        | object  | Parámetros del modelo                           |

### Campos Opcionales
| Campo             | Tipo    | Descripción                                      |
|-------------------|---------|--------------------------------------------------|
| medication_id     | int     | ID del medicamento asociado (opcional)          |
| trained_at        | string  | Fecha y hora del entrenamiento (por defecto: ahora) |

### Encabezados
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

### Respuesta Exitosa (201 Created)
```json
{
  "id": 2,
  "created_at": "2025-06-05T16:25:00.000000",
  "updated_at": "2025-06-05T16:25:00.000000",
  "model_version": "v1.2.4",
  "accuracy": 0.94,
  "mae": 1.2,
  "mse": 2.8,
  "r2_score": 0.91,
  "trained_at": "2025-06-05T16:25:00.000000",
  "training_duration": 135.2,
  "features_used": ["sales_history", "seasonality", "price", "stock_level", "promotions"],
  "parameters": {
    "learning_rate": 0.001,
    "epochs": 120,
    "batch_size": 32,
    "layers": [64, 32, 16]
  },
  "medication_id": 1
}
```

### Posibles Errores
- **400 Bad Request**: Datos de entrada inválidos o faltantes
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario no tiene permisos de administrador
- **404 Not Found**: Medicamento no encontrado (si se proporciona medication_id)

---

## Obtener Métricas por Medicamento

Obtiene las métricas de predicción para un medicamento específico.

### URL
```
GET /api/v1/prediction-metrics/medication/{medication_id}
```

### Parámetros de Ruta
| Parámetro    | Tipo | Descripción                        |
|--------------|------|------------------------------------|
| medication_id| int  | ID del medicamento a consultar      |

### Parámetros de Consulta
| Parámetro | Tipo | Requerido | Descripción                              |
|-----------|------|-----------|------------------------------------------|
| limit     | int  | No        | Límite de resultados (por defecto: 10)   |
| offset    | int  | No        | Desplazamiento para paginación            |

### Encabezados
```
Authorization: Bearer <token_jwt>
Accept: application/json
```

### Respuesta Exitosa (200 OK)
```json
[
  {
    "id": 2,
    "model_version": "v1.2.4",
    "accuracy": 0.94,
    "mae": 1.2,
    "mse": 2.8,
    "r2_score": 0.91,
    "trained_at": "2025-06-05T16:25:00.000000",
    "training_duration": 135.2,
    "features_used": ["sales_history", "seasonality", "price", "stock_level", "promotions"],
    "parameters": {
      "learning_rate": 0.001,
      "epochs": 120,
      "batch_size": 32,
      "layers": [64, 32, 16]
    },
    "medication_id": 1
  },
  {
    "id": 1,
    "model_version": "v1.2.3",
    "accuracy": 0.92,
    "mae": 1.5,
    "mse": 3.2,
    "r2_score": 0.89,
    "trained_at": "2025-06-05T15:30:00.000000",
    "training_duration": 120.5,
    "features_used": ["sales_history", "seasonality", "price", "stock_level"],
    "parameters": {
      "learning_rate": 0.001,
      "epochs": 100,
      "batch_size": 32
    },
    "medication_id": 1
  }
]
```

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario no tiene permisos suficientes
- **404 Not Found**: Medicamento no encontrado

---

## Obtener Últimas Métricas de un Medicamento

Obtiene la última métrica registrada para un medicamento específico.

### URL
```
GET /api/v1/prediction-metrics/latest/medication/{medication_id}
```

### Parámetros de Ruta
| Parámetro    | Tipo | Descripción                        |
|--------------|------|------------------------------------|
| medication_id| int  | ID del medicamento a consultar      |

### Encabezados
```
Authorization: Bearer <token_jwt>
Accept: application/json
```

### Respuesta Exitosa (200 OK)
```json
{
  "id": 2,
  "model_version": "v1.2.4",
  "accuracy": 0.94,
  "mae": 1.2,
  "mse": 2.8,
  "r2_score": 0.91,
  "trained_at": "2025-06-05T16:25:00.000000",
  "training_duration": 135.2,
  "features_used": ["sales_history", "seasonality", "price", "stock_level", "promotions"],
  "parameters": {
    "learning_rate": 0.001,
    "epochs": 120,
    "batch_size": 32,
    "layers": [64, 32, 16]
  },
  "medication_id": 1
}
```

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario no tiene permisos suficientes
- **404 Not Found**: No se encontraron métricas para el medicamento

---

## Consideraciones Adicionales

1. **Autenticación**: Todos los endpoints requieren autenticación mediante JWT.
2. **Permisos**: Algunos endpoints pueden requerir privilegios de administrador.
3. **Paginación**: Los endpoints que devuelven listas soportan paginación mediante los parámetros `limit` y `offset`.
4. **Ordenación**: Los resultados se ordenan por fecha de entrenamiento de forma descendente por defecto.
5. **Formatos de Fecha**: Todas las fechas siguen el formato ISO 8601 (ej: "2025-06-05T16:25:00.000000").
