# API de Predicciones

Esta documentación describe los endpoints disponibles para realizar predicciones de desabastecimiento de medicamentos y gestionar las predicciones almacenadas.

## Tabla de Contenidos
- [Modelo de Datos](#modelo-de-datos)
- [Predecir Desabastecimiento](#predecir-desabastecimiento)
- [Evaluar Modelo](#evaluar-modelo)
- [Obtener Métricas del Modelo](#obtener-métricas-del-modelo)
- [Gestionar Predicciones](#gestionar-predicciones)

## Modelo de Datos

### Predicción

| Campo                   | Tipo     | Requerido | Descripción                                                                 |
|-------------------------|----------|-----------|-----------------------------------------------------------------------------|
| id                     | int      | No        | ID único de la predicción (generado automáticamente)                        |
| created_at             | datetime | No        | Fecha y hora de creación (generado automáticamente)                         |
| updated_at             | datetime | No        | Fecha y hora de última actualización (generado automáticamente)             |
| date                   | datetime | Sí        | Fecha de la predicción                                                     |
| real_usage             | float    | Sí        | Uso real del medicamento (R_i)                                             |
| predicted_usage        | float    | Sí        | Uso predicho del medicamento (P_i)                                         |
| stock                  | float    | Sí        | Stock disponible al momento de la predicción                                |
| month_of_year          | int      | No        | Mes del año (1-12) para análisis estacional                                |
| regional_demand        | float    | No        | Demanda regional estimada                                                  |
| is_shortage           | bool     | No        | Indica si hay desabastecimiento (true/false)                               |
| shortage_days         | int      | No        | Días estimados hasta el desabastecimiento (si aplica)                      |
| seasonality_coefficient| float    | No        | Coeficiente de estacionalidad (1.0 = sin estacionalidad)                   |
| trend                 | string   | No        | Dirección de la tendencia ("up", "down", "stable")                        |
| alert_level           | string   | No        | Nivel de alerta ("low", "medium", "high")                                 |
| alert_message         | string   | No        | Mensaje descriptivo de la alerta                                           |
| resolved_at           | datetime | No        | Fecha de resolución de la alerta (si aplica)                              |
| confidence_interval_lower | float | No    | Límite inferior del intervalo de confianza                                 |
| confidence_interval_upper | float | No    | Límite superior del intervalo de confianza                                 |
| metadata_             | JSON     | No        | Metadatos adicionales en formato JSON                                      |
| medication_id         | int      | Sí        | ID del medicamento asociado                                                |

### Métricas del Modelo

Vea la documentación completa en [PREDICTION_METRICS.md](./PREDICTION_METRICS.md).

---

## Predecir Desabastecimiento

Obtiene una predicción de desabastecimiento para un medicamento específico.

### URL
```
GET /api/v1/predictions/predict/
```

### Parámetros de Consulta
| Parámetro    | Tipo | Requerido | Descripción                                |
|--------------|------|-----------|--------------------------------------------|
| medication_id | int  | Sí        | ID del medicamento a predecir (mayor a 0)  |
| days_ahead   | int  | No        | Días hacia adelante para la predicción (por defecto: 30) |
| include_confidence | bool | No | Incluir intervalo de confianza (por defecto: false) |

### Encabezados
```
Authorization: Bearer <token_jwt>
Accept: application/json
```

### Respuesta Exitosa (200 OK)
```json
{
  "medication_id": 1,
  "prediction": true,
  "probability": 0.85,
  "shortage_days": 45,
  "confidence_interval": {
    "lower": 0.78,
    "upper": 0.91
  },
  "timestamp": "2025-06-05T10:30:45.123456",
  "trend": "up",
  "alert_level": "medium",
  "alert_message": "Posible desabastecimiento en 45 días",
  "new_field": "new_value"
}
```

### Campos de Respuesta
| Campo               | Tipo   | Descripción                                      |
|---------------------|--------|--------------------------------------------------|
| medication_id       | int    | ID del medicamento consultado                    |
| prediction          | bool   | `true` si habrá desabastecimiento, `false` en caso contrario |
| probability         | float  | Probabilidad de la predicción (0 a 1)            |
| shortage_days       | int    | Días estimados hasta el desabastecimiento        |
| confidence_interval | object | Intervalo de confianza de la predicción           |
| confidence_interval.lower | float | Límite inferior del intervalo de confianza |
| confidence_interval.upper | float | Límite superior del intervalo de confianza |
| timestamp           | string | Fecha y hora de la predicción                    |
| trend               | string | Dirección de la tendencia ("up", "down", "stable") |
| alert_level         | string | Nivel de alerta ("low", "medium", "high")         |
| alert_message       | string | Mensaje descriptivo de la alerta                  |
| new_field           | string | Nuevo campo agregado                             |

### Posibles Errores
- **400 Bad Request**: ID de medicamento inválido o no proporcionado
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario no tiene permisos suficientes
- **404 Not Found**: Medicamento no encontrado
- **500 Internal Server Error**: Error al procesar la predicción

---

## Gestionar Predicciones

### Obtener Predicciones

Obtiene un listado de predicciones almacenadas con filtros opcionales.

#### URL
```
GET /api/v1/predictions/
```

#### Parámetros de Consulta
| Parámetro    | Tipo   | Requerido | Descripción                                |
|--------------|--------|-----------|--------------------------------------------|
| medication_id| int    | No        | Filtrar por ID de medicamento             |
| start_date   | string | No        | Fecha de inicio (formato: YYYY-MM-DD)     |
| end_date     | string | No        | Fecha de fin (formato: YYYY-MM-DD)        |
| alert_level  | string | No        | Nivel de alerta ("low", "medium", "high") |
| resolved     | bool   | No        | Filtrar por estado de resolución          |
| limit        | int    | No        | Límite de resultados (por defecto: 100)   |
| offset       | int    | No        | Desplazamiento para paginación             |

#### Encabezados
```
Authorization: Bearer <token_jwt>
Accept: application/json
```

#### Respuesta Exitosa (200 OK)
```json
{
  "items": [
    {
      "id": 1,
      "date": "2025-06-05T10:30:45.123456",
      "predicted_usage": 120.5,
      "real_usage": 118.7,
      "stock": 1500,
      "is_shortage": false,
      "shortage_days": null,
      "trend": "up",
      "alert_level": "low",
      "alert_message": "Consumo estable",
      "medication_id": 1,
      "medication_name": "Paracetamol 500mg"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### Obtener una Predicción por ID

Obtiene los detalles de una predicción específica.

#### URL
```
GET /api/v1/predictions/{prediction_id}
```

#### Parámetros de Ruta
| Parámetro    | Tipo | Descripción                |
|--------------|------|----------------------------|
| prediction_id| int  | ID de la predicción a consultar |

#### Encabezados
```
Authorization: Bearer <token_jwt>
Accept: application/json
```

#### Respuesta Exitosa (200 OK)
```json
{
  "id": 1,
  "date": "2025-06-05T10:30:45.123456",
  "real_usage": 118.7,
  "predicted_usage": 120.5,
  "stock": 1500,
  "month_of_year": 6,
  "regional_demand": 125.3,
  "is_shortage": false,
  "shortage_days": null,
  "seasonality_coefficient": 1.05,
  "trend": "up",
  "alert_level": "low",
  "alert_message": "Consumo estable",
  "resolved_at": null,
  "confidence_interval_lower": 115.2,
  "confidence_interval_upper": 125.8,
  "metadata_": {
    "model_version": "v1.2.3",
    "features_used": ["sales_history", "seasonality", "price"]
  },
  "medication_id": 1,
  "created_at": "2025-06-05T10:30:45.123456",
  "updated_at": "2025-06-05T10:30:45.123456"
}
```

### Actualizar una Predicción

Actualiza los campos de una predicción existente.

#### URL
```
PATCH /api/v1/predictions/{prediction_id}
```

#### Parámetros de Ruta
| Parámetro    | Tipo | Descripción                |
|--------------|------|----------------------------|
| prediction_id| int  | ID de la predicción a actualizar |

#### Cuerpo de la Solicitud
```json
{
  "alert_level": "medium",
  "alert_message": "Aumento en la demanda detectado",
  "resolved_at": null
}
```

#### Encabezados
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

#### Respuesta Exitosa (200 OK)
```json
{
  "id": 1,
  "alert_level": "medium",
  "alert_message": "Aumento en la demanda detectado",
  "resolved_at": null,
  "updated_at": "2025-06-05T11:15:30.000000"
}
```

### Eliminar una Predicción

Elimina una predicción existente.

#### URL
```
DELETE /api/v1/predictions/{prediction_id}
```

#### Parámetros de Ruta
| Parámetro    | Tipo | Descripción                |
|--------------|------|----------------------------|
| prediction_id| int  | ID de la predicción a eliminar |

#### Encabezados
```
Authorization: Bearer <token_jwt>
```

#### Respuesta Exitosa (204 No Content)
```
(No hay contenido en la respuesta)
```

### Notas Adicionales

1. **Permisos**:
   - Cualquier usuario autenticado puede ver las predicciones.
   - Solo los administradores pueden crear, actualizar o eliminar predicciones.

2. **Filtros**:
   - Las fechas deben estar en formato ISO 8601 (YYYY-MM-DD).
   - Los filtros se pueden combinar para refinar la búsqueda.

3. **Paginación**:
   - Use los parámetros `limit` y `offset` para la paginación.
   - La respuesta incluye el total de registros disponibles.

4. **Campos de Solo Lectura**:
   - Los campos como `id`, `created_at` y `updated_at` son gestionados por el servidor y no pueden modificarse.

5. **Campos Calculados**:
   - Algunos campos como `shortage_days` y `alert_level` pueden ser calculados automáticamente por el servidor.

---

## Evaluar Modelo

Evalúa el rendimiento del modelo de predicción (solo administradores).

### URL
```
GET /api/v1/predictions/evaluate/
```

### Parámetros de Consulta
| Parámetro    | Tipo | Requerido | Descripción                                |
|--------------|------|-----------|--------------------------------------------|
| medicamento_id | int  | Sí        | ID del medicamento a evaluar (mayor a 0)   |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
{
  "model_type": "RandomForest",
  "metrics": {
    "accuracy": 0.95,
    "precision": 0.94,
    "recall": 0.96,
    "f1_score": 0.95,
    "roc_auc": 0.98
  },
  "timestamp": "2025-05-20T11:15:30.456789"
}
```

### Campos de la Respuesta
| Campo     | Tipo  | Descripción                                      |
|-----------|-------|--------------------------------------------------|
| model_type| string| Tipo de modelo utilizado para la evaluación        |
| metrics   | object| Métricas de rendimiento del modelo               |
| timestamp | string| Fecha y hora de la evaluación                     |

### Métricas Incluidas
| Métrica   | Tipo  | Rango  | Descripción                                      |
|-----------|-------|--------|--------------------------------------------------|
| accuracy  | float | 0-1    | Precisión general del modelo                    |
| precision | float | 0-1    | Precisión de la clase positiva                  |
| recall    | float | 0-1    | Sensibilidad del modelo                         |
| f1_score  | float | 0-1    | Media armónica de precisión y recall           |
| roc_auc   | float | 0.5-1  | Área bajo la curva ROC                          |

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario sin permisos de administrador
- **404 Not Found**: Medicamento no encontrado
- **500 Internal Server Error**: Error al evaluar el modelo

---

## Obtener Métricas del Modelo

Obtiene las últimas métricas de rendimiento del modelo (solo administradores).

### URL
```
GET /api/v1/predictions/metrics
```

### Parámetros de Consulta
| Parámetro | Tipo   | Requerido | Descripción                                      |
|-----------|--------|-----------|--------------------------------------------------|
| days      | int    | No        | Número de días hacia atrás para obtener métricas (1-365, default: 30) |
| limit     | int    | No        | Número máximo de registros a devolver (1-1000, default: 100) |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
{
  "model_type": "RandomForest",
  "last_updated": "2025-05-21T22:05:26.123456",
  "metrics_history": [
    {
      "date": "2025-05-20",
      "accuracy": 0.95,
      "precision": 0.94,
      "recall": 0.96,
      "f1_score": 0.95,
      "roc_auc": 0.98
    },
    {
      "date": "2025-05-19",
      "accuracy": 0.94,
      "precision": 0.93,
      "recall": 0.95,
      "f1_score": 0.94,
      "roc_auc": 0.97
    }
  ]
}
```

### Campos de Respuesta
| Campo           | Tipo  | Descripción                                      |
|-----------------|-------|--------------------------------------------------|
| model_type      | string| Tipo de modelo utilizado (ej: "RandomForest")    |
| last_updated    | string| Fecha y hora de la última actualización          |
| metrics_history | array | Historial de métricas ordenado por fecha (más reciente primero) |

### Métricas Disponibles
- **accuracy**: Exactitud del modelo (0 a 1)
- **precision**: Precisión del modelo (0 a 1)
- **recall**: Sensibilidad del modelo (0 a 1)
- **f1_score**: Puntuación F1 (media armónica de precisión y recall)
- **roc_auc**: Área bajo la curva ROC (0.5 a 1.0)

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: El usuario no tiene permisos de administrador
- **500 Internal Server Error**: Error al obtener las métricas

### Posibles Errores
- **401 Unauthorized**: Token no proporcionado o inválido
- **403 Forbidden**: Usuario sin permisos de administrador
- **500 Internal Server Error**: Error al recuperar las métricas

---

## Notas de Uso

1. **Autenticación**: Todos los endpoints requieren autenticación mediante JWT
2. **Permisos**: Algunos endpoints están restringidos a usuarios con rol de administrador
3. **Limitaciones**: 
   - Las predicciones tienen un límite de tasa de solicitudes
   - Los modelos se actualizan periódicamente, lo que puede afectar las predicciones
4. **Precisión**: Las predicciones son estimaciones basadas en datos históricos y pueden no ser 100% precisas

---

## Códigos de Estado HTTP

| Código | Significado                               |
|--------|-------------------------------------------|
| 200    | OK - Solicitud exitosa                    |
| 201    | Creado - Recurso creado exitosamente      |
| 400    | Solicitud incorrecta                      |
| 401    | No autorizado                             |
| 403    | Prohibido - Sin permisos suficientes     |
| 404    | Recurso no encontrado                     |
| 429    | Demasiadas solicitudes                    |
| 500    | Error interno del servidor                |

---

## Ejemplo de Uso con cURL

### Realizar una predicción
```bash
curl -X GET "https://api.utcubamba.edu.pe/v1/predictions/predict/?medicamento_id=1" \
  -H "Authorization: Bearer <token_jwt>" \
  -H "accept: application/json"
```

### Evaluar el modelo (solo admin)
```bash
curl -X GET "https://api.utcubamba.edu.pe/v1/predictions/evaluate/?medicamento_id=1" \
  -H "Authorization: Bearer <token_jwt_admin>" \
  -H "accept: application/json"
```

### Obtener métricas del modelo (solo admin)
```bash
# Obtener métricas de los últimos 30 días (valor por defecto)
curl -X GET "https://api.utcubamba.edu.pe/v1/predictions/metrics" \
  -H "Authorization: Bearer <token_jwt_admin>"

# Obtener métricas de los últimos 7 días (máx. 50 registros)
curl -X GET "https://api.utcubamba.edu.pe/v1/predictions/metrics?days=7&limit=50" \
  -H "Authorization: Bearer <token_jwt_admin>"
```

### Ejemplo de respuesta de error (403 Forbidden)
```json
{
  "detail": "No tiene permisos suficientes para realizar esta acción"
}
```
