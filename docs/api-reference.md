# Utcubamba API — Documentación de Referencia

API de predicción de desabastecimiento de medicamentos. Sistema de gestión de inventario
con predicción ML, notificaciones, órdenes de reabastecimiento y reportes.

---

## Tabla de Contenidos

1. [Información General](#1-información-general)
2. [Modelo de Datos](#2-modelo-de-datos)
3. [Excepciones de Dominio](#3-excepciones-de-dominio)
4. [Endpoints — Auth](#4-endpoints--auth-apiv1auth)
5. [Endpoints — Users](#5-endpoints--users-apiv1users)
6. [Endpoints — Medications](#6-endpoints--medications-apiv1medications)
7. [Endpoints — Predictions](#7-endpoints--predictions-apiv1predictions)
8. [Endpoints — Prediction Metrics](#8-endpoints--prediction-metrics-apiv1prediction-metrics)
9. [Endpoints — Categories](#9-endpoints--categories-apiv1categories)
10. [Endpoints — Notifications](#10-endpoints--notifications-apiv1notifications)
11. [Endpoints — Orders](#11-endpoints--orders-apiv1orders)
12. [Endpoints — Reports](#12-endpoints--reports-apiv1reports)

---

## 1. Información General

| Propiedad | Valor |
|---|---|
| **Título** | Utcubamba API |
| **Versión** | 1.0.0 |
| **Base URL** | `/api/v1` |
| **Docs Swagger** | `/api/docs` |
| **Docs Redoc** | `/api/redoc` |
| **OpenAPI JSON** | `/api/openapi.json` |
| **Contacto** | `soporte@utcubamba.com` (configurable vía `CONTACT_EMAIL`) |

### Stack Tecnológico

- **Framework**: FastAPI
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Base de datos**: PostgreSQL (producción) / SQLite (tests)
- **Autenticación**: JWT (access token + cookie HttpOnly)
- **Rate Limiting**: SlowAPI
- **Tareas asíncronas**: Celery + Redis
- **Migraciones**: Alembic

### Autenticación

La API usa JWT. El token se envía como:
- **Header**: `Authorization: Bearer <token>`

Configuración por defecto: token expira en 30 minutos (`ACCESS_TOKEN_EXPIRE_MINUTES`).

### Roles de Usuario

| Rol | Descripción |
|---|---|
| `admin` | Acceso total al sistema |
| `user` | Usuario estándar |
| `farmacia` | Personal de farmacia |
| `enfermeria` | Personal de enfermería |

### Estados de Usuario

| Estado | Descripción |
|---|---|
| `activo` | Usuario activo |
| `dado_de_baja` | Usuario desactivado |

### Middleware

- **CORS**: Orígenes configurados vía `CORS_ORIGINS` (default: `http://localhost:3000,http://127.0.0.1:3000`)
- **Rate Limiting**: SlowAPI con SlowAPIMiddleware
- **Exception Handlers**:
  - `DomainError` → HTTP 400/403/404/500 según subtipo
  - `RateLimitExceeded` → HTTP 429
  - `RequestValidationError` → HTTP 422
  - `Exception` (catch-all) → HTTP 500

---

## 2. Modelo de Datos

### Diagrama de Entidades

**users** → `password_reset_tokens`, `notifications`, `orders` (created_by), `reports` (generated_by)
**medications** → `movements`, `predictions`, `orders`, `medication_condition`, `categories`, `intake_types`
**categories** → `medications`
**intake_types** → `medications`
**conditions** → `medication_condition` → `medications` (many-to-many)
**prediction_metrics** → `predictions`
**movements** → `predictions`

### Entidades y Columnas

#### `users`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| nombre | str(100) | NOT NULL |
| email | str(255) | UNIQUE, INDEX, NOT NULL |
| hashed_password | str(255) | NOT NULL |
| cargo | str(100) | NOT NULL |
| departamento | str(100) | NOT NULL |
| contacto | str(50) | UNIQUE, INDEX, nullable |
| fecha_ingreso | datetime | default: now() |
| estado | enum(activo, dado_de_baja) | default: activo |
| role | enum(admin, user, farmacia, enfermeria) | default: user |
| created_at | datetime | |
| updated_at | datetime | |

#### `medications`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| name | str(100) | INDEX, NOT NULL |
| description | str(500) | nullable |
| stock | int | ge=0, default: 0 |
| min_stock | int | ge=0, default: 10 |
| unit | str(50) | default: "units" |
| manufacturer | str(200) | nullable |
| expiration_date | datetime | nullable |
| status | str(50) | default: "Activo" |
| price | float | ge=0, default: 0.0 |
| category_id | int | FK → categories.id, nullable |
| intake_type_id | int | FK → intake_types.id, nullable |
| created_at | datetime | |
| updated_at | datetime | |

#### `categories`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| name | str(100) | UNIQUE, INDEX, NOT NULL |
| description | str(500) | nullable |
| created_at | datetime | |
| updated_at | datetime | |

#### `intake_types`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| name | str(100) | UNIQUE, INDEX, NOT NULL |
| description | str(500) | nullable |
| created_at | datetime | |
| updated_at | datetime | |

#### `conditions`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| name | str(100) | UNIQUE, INDEX, NOT NULL |
| description | str(500) | nullable |
| created_at | datetime | |
| updated_at | datetime | |

#### `medication_condition` (join table)
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK, INDEX |
| medication_id | int | FK → medications.id, INDEX |
| condition_id | int | FK → conditions.id, INDEX |

#### `movements`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| date | datetime | default: now() |
| type | enum(in, out) | NOT NULL |
| quantity | float | gt=0 |
| notes | str(500) | nullable |
| medication_id | int | FK → medications.id |
| created_at | datetime | |
| updated_at | datetime | |

#### `predictions`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| date | datetime | default: now() |
| real_usage | float | ge=0 |
| predicted_usage | float | gt=0 |
| stock | float | ge=0 |
| month_of_year | int | 1-12 |
| regional_demand | float | ge=0 |
| restock_time | float | nullable, ge=0 |
| shortage | bool | default: false |
| probability | float | 0-1, nullable |
| seasonality_coefficient | float | 0-1, nullable |
| trend | enum(up, down, stable) | nullable |
| alert_level | enum(low, medium, high) | nullable |
| alert_message | str(500) | nullable |
| resolved_at | datetime | nullable |
| confidence_interval_lower | float | ge=0, nullable |
| confidence_interval_upper | float | ge=0, nullable |
| metadata_ | JSON | default: {} |
| medication_id | int | FK → medications.id |
| movement_id | int | FK → movements.id, nullable |
| prediction_metrics_id | int | FK → prediction_metrics.id, nullable |
| created_at | datetime | |
| updated_at | datetime | |

#### `prediction_metrics`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| model_version | str(50) | NOT NULL |
| accuracy | float | 0-1 |
| mae | float | ge=0 |
| mse | float | ge=0 |
| r2_score | float | |
| trained_at | datetime | default: now() |
| training_duration | float | nullable, ge=0 |
| features_used | JSON | default: [] |
| parameters | JSON | default: {} |
| medication_id | int | FK → medications.id, nullable |
| created_at | datetime | |
| updated_at | datetime | |

#### `notifications`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| title | str(200) | NOT NULL |
| message | str(2000) | NOT NULL |
| type | enum | shortage_alert, stock_alert, order_update, system, info |
| level | enum | low, medium, high |
| read | bool | default: false |
| related_entity_type | str(50) | nullable |
| related_entity_id | int | nullable |
| resolved_at | datetime | nullable |
| metadata_ | JSON | default: {} |
| user_id | int | FK → users.id |
| created_at | datetime | |
| updated_at | datetime | |
| **Índice** | | `ix_notifications_user_read_created` (user_id, read, created_at) |

#### `orders`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| quantity | int | gt=0 |
| status | enum | pending, approved, shipped, received, cancelled |
| order_date | datetime | default: now() |
| received_date | datetime | nullable |
| supplier | str(200) | NOT NULL |
| total_cost | float | ge=0 |
| notes | str(1000) | nullable |
| medication_id | int | FK → medications.id |
| created_by | int | FK → users.id |
| created_at | datetime | |
| updated_at | datetime | |

#### `reports`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| title | str(200) | NOT NULL |
| type | enum | inventory, movements, trends, alerts, financial, patients |
| format | enum | pdf, excel, csv |
| status | enum | generating, completed, failed |
| parameters | JSON | default: {} |
| data | JSON | default: {} |
| file_path | str(500) | nullable |
| error_message | str(1000) | nullable |
| generated_by | int | FK → users.id |
| generated_at | datetime | default: now() |
| created_at | datetime | |
| updated_at | datetime | |

#### `password_reset_tokens`
| Columna | Tipo | Restricciones |
|---|---|---|
| id | int | PK |
| token | str(255) | UNIQUE, NOT NULL |
| expires_at | datetime | default: now() + 1h |
| user_id | int | FK → users.id |
| created_at | datetime | |
| updated_at | datetime | |

---

## 3. Excepciones de Dominio

El servicio lanza excepciones de dominio que son convertidas automáticamente a respuestas HTTP
por el handler global en `main.py`.

| Excepción | HTTP Status | Descripción |
|---|---|---|
| `NotFoundError` | 404 | Entidad no encontrada (base) |
| `MedicationNotFoundError` | 404 | Medicamento no encontrado |
| `OrderNotFoundError` | 404 | Orden no encontrada |
| `ReportNotFoundError` | 404 | Reporte no encontrado |
| `NotificationNotFoundError` | 404 | Notificación no encontrada |
| `CategoryNotFoundError` | 404 | Categoría no encontrada |
| `IntakeTypeNotFoundError` | 404 | Tipo de ingesta no encontrado |
| `ConditionNotFoundError` | 404 | Condición no encontrada |
| `ForbiddenError` | 403 | Sin permisos |
| `ValidationError` | 400 | Error de validación |

Formato de respuesta error:
```json
{ "detail": "<mensaje>" }
```

---

## 4. Endpoints — Auth (`/api/v1/auth`)

---

### `POST /auth/login`

Inicia sesión y devuelve un token JWT.

**Request Body:**
```json
{
  "username": "usuario@email.com",
  "password": "miclave123"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "email": "usuario@email.com",
    "role": "admin",
    "status": "activo"
  }
}
```
También setea cookie `access_token` (HttpOnly, SameSite=Lax, Secure en producción).
Rate limit: 10 requests/minuto.

**Errores:** 401 (credenciales inválidas), 429 (rate limit), 422 (validación)

---

### `POST /auth/register`

Registra un nuevo usuario.

**Rate limit:** 5 requests/minuto.

**Request Body:**
```json
{
  "name": "Juan Pérez",
  "email": "juan.perez@gmail.com",
  "password": "miclave123",
  "cargo": "Farmacéutico",
  "departamento": "Farmacia",
  "contacto": "+51987654321",
  "role": "user"
}
```

**Response 201:**
```json
{
  "message": "Usuario registrado exitosamente",
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": { "email": "...", "role": "user", "status": "activo" }
}
```

**Errores:** 400, 422, 429, 500

---

### `POST /auth/logout`

Cierra sesión eliminando la cookie `access_token`.

**Response 200:**
```json
{ "message": "Sesión cerrada exitosamente" }
```

---

### `POST /auth/password-reset`

Solicita un token de restablecimiento de contraseña. Envía email si el usuario existe
(siempre devuelve el mismo mensaje por seguridad).

**Request Body:**
```json
{ "email": "usuario@utcubamba.edu.pe" }
```

**Response 200:**
```json
{ "message": "Si tu correo está registrado, recibirás un enlace para restablecer tu contraseña" }
```

---

### `POST /auth/password-reset/confirm`

Restablece la contraseña usando un token.

**Request Body:**
```json
{
  "token": "abc123...",
  "new_password": "nuevaClave456"
}
```

**Response 200:**
```json
{ "message": "Contraseña restablecida exitosamente" }
```

**Errores:** 400 (token inválido/expirado), 422

---

## 5. Endpoints — Users (`/api/v1/users`)

---

### `GET /users` — [ADMIN]

Lista todos los usuarios.

**Query params:** `skip` (default: 0), `limit` (default: 100)

**Response 200:** `List[UserResponse]`
```json
[{
  "email": "user@test.com",
  "nombre": "User Test",
  "cargo": "Farmacéutico",
  "departamento": "Farmacia",
  "contacto": null,
  "role": "user",
  "estado": "activo",
  "id": 1,
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}]
```

**Errores:** 403 (no admin)

---

### `GET /users/me`

Obtiene los datos del usuario autenticado.

**Response 200:** `UserResponse`

---

### `GET /users/{user_id}` — [ADMIN]

Obtiene un usuario específico por ID.

**Errores:** 403, 404

---

### `PUT /users/me`

Actualiza los datos del usuario autenticado.

**Request Body** (todos opcionales):
```json
{
  "nombre": "Nuevo Nombre",
  "cargo": "Nuevo Cargo",
  "departamento": "Nuevo Depto",
  "contacto": "+51987654321"
}
```

**Restricciones:**
- Usuarios no-admin solo pueden actualizar: `nombre`, `cargo`, `departamento`, `contacto`
- Admin puede actualizar también `role` y `email`
- `contacto` debe ser único en el sistema

**Errores:** 400 (contacto duplicado, rol inválido, sin campos válidos), 500

---

### `PUT /users/admin/{user_id}` — [ADMIN]

Admin actualiza cualquier usuario.

**Request Body** (todos opcionales):
```json
{
  "nombre": "Nuevo Nombre",
  "email": "nuevo@email.com",
  "role": "admin",
  "estado": "activo"
}
```

**Errores:** 403, 404, 400

---

## 6. Endpoints — Medications (`/api/v1/medications`)

---

### `GET /medications/test`

Endpoint de prueba (sin autenticación).

**Response 200:**
```json
{ "message": "El endpoint de medicamentos está funcionando correctamente" }
```

---

### `GET /medications/`

Lista paginada de medicamentos con filtros.

**Query params:** `skip` (default: 0), `limit` (default: 10, max: 100),
`name` (búsqueda parcial LIKE), `category_id`, `intake_type_id`

**Response 200:**
```json
{
  "status": "success",
  "total": 50,
  "skip": 0,
  "limit": 10,
  "count": 10,
  "items": [{
    "id": 1,
    "name": "Paracetamol",
    "description": "...",
    "stock": 150,
    "min_stock": 50,
    "unit": "mg",
    "manufacturer": "Genfar",
    "expiration_date": "2026-01-01T00:00:00",
    "status": "Activo",
    "price": 12.50,
    "category_id": 1,
    "intake_type_id": 1,
    "created_at": "...",
    "updated_at": "...",
    "condition_ids": [1, 2],
    "category": { "id": 1, "name": "Analgésicos", "description": null }
  }]
}
```

---

### `GET /medications/{medication_id}`

Obtiene un medicamento por ID.

**Response 200:**
```json
{
  "status": "success",
  "data": { "... MedicationResponse ..." }
}
```

**Errores:** 404

---

### `POST /medications/` — [ADMIN]

Crea un nuevo medicamento.

**Request Body:**
```json
{
  "name": "Paracetamol 500mg",
  "description": "Analgésico y antipirético",
  "stock": 200,
  "min_stock": 50,
  "unit": "mg",
  "manufacturer": "Genfar",
  "expiration_date": "2026-12-31T00:00:00",
  "status": "Activo",
  "price": 15.00,
  "category_id": 1,
  "intake_type_id": 1,
  "condition_ids": [1, 2]
}
```

**Response 201:** `MedicationResponse`

**Errores:** 403, 404 (categoría/tipo ingesta/condición no encontrados vía excepción de dominio)

---

### `PUT /medications/{medication_id}` — [ADMIN]

Actualiza un medicamento.

**Request Body** (todos opcionales):
```json
{
  "name": "Paracetamol 1g",
  "stock": 180,
  "condition_ids": [1]
}
```

**Response 200:** `MedicationResponse`

**Errores:** 403, 404 (MedicationNotFoundError)

---

### `DELETE /medications/{medication_id}` — [ADMIN]

Elimina un medicamento.

**Response 204:** Sin contenido.

**Errores:** 403, 404 (MedicationNotFoundError)

---

## 7. Endpoints — Predictions (`/api/v1/predictions`)

---

### `GET /predictions/test`

Endpoint de prueba.

**Response 200:**
```json
{ "message": "Predictions endpoint is working!" }
```

---

### `GET /predictions/`

Lista paginada de predicciones.

**Query params:** `medication_id` (filtro), `skip` (default: 0), `limit` (default: 100, max: 1000)

**Response 200:**
```json
{
  "total": 150,
  "predictions": [
    {
      "medication_id": 1,
      "prediction": "shortage",
      "probability": 0.85,
      "timestamp": "2025-07-06T17:18:18.123456"
    }
  ]
}
```

---

### `GET /predictions/predict/`

Predice riesgo de desabastecimiento para un medicamento usando modelo Random Forest.

**Query params:** `medicamento_id` (requerido, >0), `dias_prediccion` (default: 30, 1-90)

**Response 200:**
```json
{
  "id": 101,
  "medication_id": 1,
  "date": "2025-07-06T17:18:18.123456",
  "real_usage": 0.0,
  "predicted_usage": 25.5,
  "stock": 150,
  "month_of_year": 7,
  "regional_demand": 0.0,
  "shortage": false,
  "probability": 0.15,
  "confidence_interval_lower": 18.2,
  "confidence_interval_upper": 32.8,
  "alert_level": "low",
  "trend": "stable",
  "seasonality_coefficient": 0.9,
  "created_at": "...",
  "updated_at": "..."
}
```

**Errores:** 404 (medicamento no encontrado), 500

---

### `GET /predictions/metrics/` — [ADMIN]

Obtiene métricas históricas del modelo de predicción.

**Query params:** `days` (default: 30, max: 365), `limit` (default: 100, max: 1000)

**Response 200:**
```json
{
  "model_type": "RandomForestRegressor",
  "last_updated": "2025-07-06T17:30:00",
  "metrics_history": [
    { "date": "2025-07-05T10:00:00", "mae": 5.2, "mse": 42.3, "r2": 0.85 }
  ]
}
```

**Errores:** 403

---

### `GET /predictions/history/`

Historial de predicciones con filtros.

**Query params:** `medication_id`, `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD),
`limit` (default: 100, max: 1000), `offset` (default: 0)

**Response 200:** `List[PredictionResponse]`

---

### `GET /predictions/seasonality`

Métricas de estacionalidad por medicamento.

**Query params:** `min_coefficient` (default: 0.1), `limit` (default: 100, max: 1000)

**Response 200:**
```json
[{
  "medication_id": 1,
  "medication_name": "Paracetamol",
  "seasonality_coefficient": 0.5234,
  "period": "monthly",
  "last_updated": "..."
}]
```

---

### `GET /predictions/demand-trend`

Analiza la tendencia general de la demanda.

**Query params:** `period` (day/week/month/quarter/year, default: month),
`lookback` (1-24, default: 6)

**Response 200:**
```json
{
  "period": "month",
  "trend": "up",
  "confidence": 0.87,
  "change_percentage": 15.23
}
```

---

### `GET /predictions/evaluate/` — [ADMIN]

Evalúa el modelo de predicción para un medicamento.

**Query params:** `medicamento_id` (requerido, >0)

**Response 200:**
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
  "timestamp": "..."
}
```

**Errores:** 403, 404

---

### `GET /predictions/uso-historico/`

Obtiene el uso histórico de un medicamento por mes y año.

**Query params:** `medicamento_id` (requerido), `mes` (1-12), `anio` (2000-2100)

**Response 200:**
```json
{
  "medication_id": 1,
  "month": 7,
  "year": 2025,
  "real_usage_total": 450.5,
  "predicted_usage_total": 500.0,
  "records": 31,
  "items": [
    { "id": 1, "date": "2025-07-01T00:00:00", "real_usage": 15.0, "predicted_usage": 16.5, "stock": 150 }
  ]
}
```

**Errores:** 404 (medicamento o datos no encontrados)

---

## 8. Endpoints — Prediction Metrics (`/api/v1/prediction-metrics`)

---

### `GET /prediction-metrics/` — [ADMIN]

Obtiene métricas de modelos de predicción con filtros.

**Query params:** `medication_id`, `model_version`, `days` (default: 30, 0=sin filtro),
`limit` (default: 100, max: 1000)

**Response 200:** `List[PredictionMetricsResponse]`
```json
[{
  "id": 1,
  "model_version": "v1.2.3",
  "accuracy": 0.95,
  "mae": 12.5,
  "mse": 250.75,
  "r2_score": 0.92,
  "trained_at": "...",
  "training_duration": 3600.5,
  "features_used": ["sales_history", "seasonality"],
  "parameters": { "n_estimators": 100 },
  "medication_id": 1,
  "created_at": "...",
  "updated_at": "..."
}]
```

---

### `GET /prediction-metrics/{metrics_id}` — [ADMIN]

Obtiene métricas por ID.

**Errores:** 403, 404

---

### `POST /prediction-metrics/` — [ADMIN]

Registra nuevas métricas de modelo. Si ya existe una métrica con la misma
`model_version` + `medication_id`, la actualiza.

**Request Body:**
```json
{
  "model_version": "v1.2.3",
  "accuracy": 0.95,
  "mae": 12.5,
  "mse": 250.75,
  "r2_score": 0.92,
  "training_duration": 3600.5,
  "features_used": ["sales_history", "seasonality", "price"],
  "parameters": { "n_estimators": 100, "max_depth": 10 },
  "medication_id": 1
}
```

**Response 201:** `PredictionMetricsResponse`

---

### `GET /prediction-metrics/medication/{medication_id}`

Obtiene métricas por medicamento.

**Query params:** `limit` (default: 10, max: 100)

**Errores:** 403, 404 (medicamento no encontrado)

---

### `GET /prediction-metrics/latest/medication/{medication_id}`

Obtiene las métricas más recientes para un medicamento.

**Errores:** 403, 404

---

### `GET /prediction-metrics/{metrics_id}/predictions`

Obtiene predicciones generadas por un modelo específico.

**Query params:** `limit` (default: 100, max: 1000)

**Errores:** 404 (modelo o predicciones no encontrados)

---

## 9. Endpoints — Categories (`/api/v1/categories`)

---

### `GET /categories/`

Lista de categorías.

**Query params:** `skip` (default: 0), `limit` (default: 100, max: 1000)

**Response 200:** `List[CategoryResponse]`
```json
[{
  "name": "Analgésicos",
  "description": "...",
  "id": 1,
  "created_at": "...",
  "updated_at": "..."
}]
```

---

### `GET /categories/{category_id}`

Obtiene una categoría por ID.

**Errores:** 404

---

## 10. Endpoints — Notifications (`/api/v1/notifications`)

---

### `GET /notifications/`

Lista notificaciones del usuario autenticado.

**Query params:** `unread_only` (bool, default: false), `skip` (0), `limit` (50, max: 200)

**Response 200:** `List[NotificationResponse]`
```json
[{
  "title": "Alerta de stock",
  "message": "El medicamento 'Paracetamol' tiene riesgo de desabastecimiento",
  "type": "shortage_alert",
  "level": "high",
  "read": false,
  "related_entity_type": "medication",
  "related_entity_id": 1,
  "metadata_": {},
  "user_id": 1,
  "id": 1,
  "created_at": "...",
  "updated_at": "..."
}]
```

---

### `GET /notifications/unread-count`

Cantidad de notificaciones no leídas del usuario.

**Response 200:**
```json
{ "count": 5 }
```

---

### `PUT /notifications/{notification_id}/read`

Marca una notificación como leída.

**Errores:** 404 (NotificationNotFoundError)

---

### `PUT /notifications/read-all`

Marca todas las notificaciones del usuario como leídas.

**Response 200:**
```json
{ "message": "3 notificaciones marcadas como leídas", "count": 3 }
```

---

### `DELETE /notifications/{notification_id}`

Elimina una notificación.

**Response 204:** Sin contenido.

**Errores:** 404 (NotificationNotFoundError)

---

## 11. Endpoints — Orders (`/api/v1/orders`)

---

### `GET /orders/`

Lista de órdenes.

**Query params:** `medication_id`, `status` (PENDING/APPROVED/SHIPPED/RECEIVED/CANCELLED),
`skip` (0), `limit` (100, max: 500)

**Response 200:** `List[OrderResponse]`
```json
[{
  "quantity": 100,
  "supplier": "Distribuidora XYZ",
  "total_cost": 1500.00,
  "notes": "Urgente",
  "medication_id": 1,
  "id": 1,
  "status": "pending",
  "order_date": "...",
  "received_date": null,
  "created_by": 1,
  "created_at": "...",
  "updated_at": "..."
}]
```

---

### `GET /orders/{order_id}`

Obtiene una orden por ID.

**Errores:** 404

---

### `POST /orders/` — [ADMIN, FARMACIA]

Crea una nueva orden de pedido.

**Request Body:**
```json
{
  "quantity": 100,
  "supplier": "Distribuidora XYZ",
  "total_cost": 1500.00,
  "notes": "Pedido mensual",
  "medication_id": 1
}
```

**Response 201:** `OrderResponse`

**Errores:** 403, 404 (MedicationNotFoundError vía excepción de dominio)

---

### `PUT /orders/{order_id}` — [ADMIN, FARMACIA]

Actualiza una orden existente.

**Request Body** (todos opcionales):
```json
{
  "quantity": 200,
  "supplier": "Nuevo Proveedor",
  "notes": "Actualizado"
}
```

**Errores:** 403, 404 (OrderNotFoundError)

---

### `PUT /orders/{order_id}/status` — [ADMIN, FARMACIA]

Actualiza el estado de una orden. Si el estado cambia a `received`,
incrementa automáticamente el `stock` del medicamento.

**Request Body:**
```json
{
  "status": "received",
  "received_date": "2025-07-06T12:00:00"
}
```

**Errores:** 403, 404 (OrderNotFoundError)

---

### `DELETE /orders/{order_id}` — [ADMIN]

Elimina una orden.

**Response 204:** Sin contenido.

**Errores:** 403, 404 (OrderNotFoundError)

---

### `GET /orders/medication/{medication_id}`

Órdenes asociadas a un medicamento.

**Query params:** `skip` (0), `limit` (50, max: 200)

**Response 200:** `List[OrderResponse]`

---

## 12. Endpoints — Reports (`/api/v1/reports`)

---

### `GET /reports/`

Lista de reportes. Admin ve todos; otros usuarios ven solo los propios.

**Query params:** `type` (inventory/movements/trends/alerts/financial/patients),
`skip` (0), `limit` (50, max: 200)

**Response 200:** `List[ReportResponse]`
```json
[{
  "title": "Inventario Julio 2025",
  "type": "inventory",
  "format": "pdf",
  "parameters": { "period": "monthly" },
  "id": 1,
  "status": "completed",
  "data": { "total_medications": 50, "medications": [...] },
  "file_path": null,
  "error_message": null,
  "generated_by": 1,
  "generated_at": "...",
  "created_at": "...",
  "updated_at": "..."
}]
```

---

### `GET /reports/{report_id}`

Obtiene un reporte por ID.

**Errores:** 404 (ReportNotFoundError), 403 (sin permisos)

---

### `POST /reports/`

Genera un nuevo reporte.

**Request Body:**
```json
{
  "title": "Inventario Mensual",
  "type": "inventory",
  "format": "pdf",
  "parameters": { "period": "monthly" }
}
```

**Response 201:** `ReportResponse`

Los tipos de reporte generan datos diferentes:

| Tipo | Contenido del `data` |
|---|---|
| `inventory` | `{ total_medications, medications: [{id, name, stock, min_stock, status}] }` |
| `movements` | `{ movements: [{type, count, total_quantity}], period }` |
| `trends` | `{ trends: [{medication_id, medication_name, avg_predicted_usage, trend}] }` |
| `alerts` | `{ total_alerts, alerts: [{medication_id, probability, alert_level, date}] }` |
| `financial` | `{ total_orders, total_cost, period }` |
| `patients` | `{ message: "Reporte de pacientes: datos no disponibles actualmente", period }` |

El reporte se crea inicialmente con status `generating`, se genera el contenido
y se actualiza a `completed` o `failed`.

---

### `DELETE /reports/{report_id}`

Elimina un reporte. Admin puede eliminar cualquiera;
otros usuarios solo los propios.

**Response 204:** Sin contenido.

**Errores:** 404 (ReportNotFoundError), 403
