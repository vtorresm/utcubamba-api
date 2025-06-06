# API de Métricas de Predicción

Esta documentación describe los endpoints disponibles para gestionar las métricas de los modelos de predicción.

## Tabla de Contenidos
- [Obtener Todas las Métricas](#obtener-todas-las-métricas)
- [Obtener Métrica por ID](#obtener-métrica-por-id)
- [Crear Nueva Métrica](#crear-nueva-métrica)
- [Obtener Métricas por Medicamento](#obtener-métricas-por-medicamento)
- [Obtener Últimas Métricas de un Medicamento](#obtener-últimas-métricas-de-un-medicamento)
- [Obtener Predicciones por Modelo](#obtener-predicciones-por-modelo)

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

## Obtener Predicciones por Modelo

Obtiene todas las predicciones generadas por un modelo de predicción específico.

### URL
```
GET /api/v1/prediction-metrics/{metric_id}/predictions
```

### Parámetros de Ruta
| Parámetro | Tipo | Descripción                |
|-----------|------|----------------------------|
| metric_id | int  | ID de la métrica del modelo |

### Parámetros de Consulta
| Parámetro | Tipo | Requerido | Descripción                              |
|-----------|------|-----------|------------------------------------------|
| limit     | int  | No        | Límite de resultados (por defecto: 100)  |

### Encabezados
```
Authorization: Bearer <token_jwt>
Accept: application/json
```

### Respuesta Exitosa (200 OK)
```json
[
  {
    "id": 101,
    "medication_id": 1,
    "date": "2025-06-01T00:00:00",
    "predicted_value": 150,
    "actual_value": 145,
    "probability": 0.87,
    "confidence_interval_lower": 120,
    "confidence_interval_upper": 180,
    "alert_level": "medium",
    "trend": "up",
    "seasonality_coefficient": 1.2,
    "created_at": "2025-06-01T10:30:00.000000"
  },
  {
    "id": 102,
    "medication_id": 1,
    "date": "2025-05-31T00:00:00",
    "predicted_value": 140,
    "actual_value": 138,
    "probability": 0.82,
    "confidence_interval_lower": 110,
    "confidence_interval_upper": 170,
    "alert_level": "low",
    "trend": "stable",
    "seasonality_coefficient": 1.1,
    "created_at": "2025-05-31T10:30:00.000000"
  }
]
```

### Campos de Respuesta
| Campo                     | Tipo    | Descripción                                      |
|---------------------------|---------|--------------------------------------------------|
| id                        | int     | ID único de la predicción                       |
| medication_id            | int     | ID del medicamento                              |
| date                     | string  | Fecha de la predicción (YYYY-MM-DD)             |
| predicted_value          | float   | Valor predicho                                  |
| actual_value             | float   | Valor real (si está disponible)                 |
| probability              | float   | Probabilidad de desabastecimiento (0-1)         |
| confidence_interval_lower| float   | Límite inferior del intervalo de confianza      |
| confidence_interval_upper| float   | Límite superior del intervalo de confianza      |
| alert_level              | string  | Nivel de alerta (low/medium/high)               |
| trend                   | string  | Tendencia (up/down/stable)                      |
| seasonality_coefficient | float   | Coeficiente de estacionalidad                   |
| created_at              | string  | Fecha y hora de creación del registro           |

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario no tiene permisos suficientes
- **404 Not Found**: No se encontró el modelo o no tiene predicciones

## Consideraciones Adicionales

1. **Autenticación**: Todos los endpoints requieren autenticación mediante JWT.
2. **Permisos**: Algunas operaciones pueden requerir permisos de administrador.
3. **Paginación**: Los endpoints que devuelven listas soportan paginación mediante los parámetros `limit` y `offset`.
4. **Filtros**: Se pueden aplicar filtros para obtener resultados más específicos.
5. **Formatos de Fecha**: Todas las fechas siguen el formato ISO 8601 (ej: "2025-06-05T16:25:00.000000").
