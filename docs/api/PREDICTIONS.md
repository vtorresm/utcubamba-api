# API de Predicciones

Esta documentación describe los endpoints disponibles para realizar predicciones de desabastecimiento de medicamentos.

## Tabla de Contenidos
- [Predecir Desabastecimiento](#predecir-desabastecimiento)
- [Evaluar Modelo](#evaluar-modelo)
- [Obtener Métricas del Modelo](#obtener-métricas-del-modelo)

---

## Predecir Desabastecimiento

Realiza una predicción de desabastecimiento para un medicamento específico.

### URL
```
GET /api/v1/predictions/predict/{medication_id}
```

### Parámetros de Ruta
| Parámetro    | Tipo | Requerido | Descripción                |
|--------------|------|-----------|----------------------------|
| medication_id| int  | Sí        | ID del medicamento a predecir |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
{
  "medication_id": 1,
  "prediction": "Sí",
  "probability": 0.85,
  "timestamp": "2025-05-20T10:30:45.123456"
}
```

### Campos de la Respuesta
| Campo        | Tipo   | Descripción                                      |
|--------------|--------|--------------------------------------------------|
| medication_id| int    | ID del medicamento consultado                    |
| prediction   | string | "Sí" o "No" indicando si habrá desabastecimiento |
| probability  | float  | Probabilidad de la predicción (0 a 1)            |
| timestamp    | string | Fecha y hora de la predicción                    |

### Posibles Errores
- **400 Bad Request**: ID de medicamento inválido
- **401 Unauthorized**: Token no proporcionado o inválido
- **404 Not Found**: Medicamento no encontrado
- **500 Internal Server Error**: Error al procesar la predicción

---

## Evaluar Modelo

Evalúa el rendimiento del modelo de predicción (solo administradores).

### URL
```
GET /api/v1/predictions/evaluate/{medication_id}
```

### Parámetros de Ruta
| Parámetro    | Tipo | Requerido | Descripción                |
|--------------|------|-----------|----------------------------|
| medication_id| int  | Sí        | ID del medicamento a evaluar |

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
| days      | int    | No        | Número de días hacia atrás para obtener métricas |
| limit     | int    | No        | Número máximo de registros a devolver           |

### Encabezados
```
Authorization: Bearer <token_jwt>
```

### Respuesta Exitosa (200 OK)
```json
{
  "model_type": "RandomForest",
  "last_updated": "2025-05-20T11:15:30.456789",
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
curl -X GET "https://api.utcubamba.edu.pe/v1/predictions/predict/1" \
  -H "Authorization: Bearer <token_jwt>"
```

### Evaluar el modelo (admin)
```bash
curl -X GET "https://api.utcubamba.edu.pe/v1/predictions/evaluate/1" \
  -H "Authorization: Bearer <token_jwt_admin>"
```

### Obtener métricas del modelo (admin)
```bash
curl -X GET "https://api.utcubamba.edu.pe/v1/predictions/metrics?days=7" \
  -H "Authorization: Bearer <token_jwt_admin>"
```
