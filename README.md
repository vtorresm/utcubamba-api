# Utcubamba API

API REST para la gestión de usuarios, medicamentos, órdenes de reabastecimiento,
notificaciones y predicción de desabastecimientos en el sistema de farmacia
de la red de salud Utcubamba.

## Tecnologías

| Categoría | Tecnología |
|---|---|
| **Framework** | FastAPI |
| **ORM** | SQLModel (SQLAlchemy + Pydantic) |
| **Base de datos** | PostgreSQL |
| **Migraciones** | Alembic |
| **Autenticación** | JWT |
| **Rate limiting** | SlowAPI |
| **Tareas asíncronas** | Celery + Redis |
| **Correo** | Mailtrap (desarrollo) |
| **ML** | Scikit-learn (Random Forest) |
| **Servidor** | Uvicorn |
| **Tests** | pytest + httpx (TestClient) |

## Características

- Autenticación y autorización con JWT (token + cookie HttpOnly)
- Gestión de usuarios con 4 roles (admin, user, farmacia, enfermeria)
- CRUD completo de medicamentos con categorías, tipos de ingesta y condiciones
- Órdenes de pedido con actualización automática de stock al recibir
- Notificaciones y alertas con niveles de prioridad
- Reportes generados con datos agregados en JSON
- Predicción de desabastecimientos con Random Forest
- Análisis de tendencias y estacionalidad
- Rate limiting por endpoint
- CORS configurable
- Documentación interactiva con Swagger y ReDoc
- Tareas programadas vía Celery (batch predictions, low stock alerts, cleanup)

## Estructura del proyecto

```
utcubamba-api/
├── src/
│   ├── api/v1/
│   │   ├── router.py                     # Montaje de rutas
│   │   └── endpoints/
│   │       ├── auth.py                   # Login, registro, password reset
│   │       ├── users.py                  # CRUD de usuarios
│   │       ├── medications.py            # CRUD de medicamentos
│   │       ├── categories.py             # Categorías de medicamentos
│   │       ├── predictions.py            # Predicciones y análisis ML
│   │       ├── prediction_metrics.py     # Métricas de modelos
│   │       ├── notifications.py          # Notificaciones y alertas
│   │       ├── orders.py                 # Órdenes de reabastecimiento
│   │       └── reports.py                # Reportes del sistema
│   ├── core/
│   │   ├── config.py                     # Configuración vía Pydantic Settings
│   │   ├── database.py                   # Engine y sesión SQLModel
│   │   ├── limiter.py                    # Rate limiter SlowAPI
│   │   ├── logging.py                    # Configuración de logs
│   │   └── security.py                   # Utilidades de seguridad
│   ├── dependencies/
│   │   └── auth.py                       # Dependencia get_current_user
│   ├── exceptions.py                     # Excepciones de dominio
│   ├── models/                           # Modelos SQLModel (14 tablas)
│   │   ├── base.py                       # Base, Role, UserStatus
│   │   ├── user.py
│   │   ├── medication.py
│   │   ├── category.py
│   │   ├── intake_type.py
│   │   ├── condition.py
│   │   ├── medication_condition.py       # Join table (many-to-many)
│   │   ├── movement.py
│   │   ├── prediction.py                 # Predicciones + PredictionMetrics
│   │   ├── notification.py
│   │   ├── order.py
│   │   ├── report.py
│   │   └── password_reset_token.py
│   ├── schemas/                          # Esquemas Pydantic v2
│   │   ├── user.py
│   │   ├── medication.py
│   │   ├── category.py
│   │   ├── prediction.py
│   │   ├── notification.py
│   │   ├── order.py
│   │   └── report.py
│   ├── services/                         # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── email_service.py
│   │   ├── medication_service.py
│   │   ├── notification_service.py
│   │   ├── order_service.py
│   │   ├── prediction_service.py
│   │   ├── report_service.py
│   │   └── user_service.py
│   ├── tasks/
│   │   ├── celery_app.py                 # Configuración Celery
│   │   └── tasks.py                      # Tareas programadas
│   └── main.py                           # Punto de entrada
├── alembic/                              # Migraciones
│   └── versions/
├── docs/
│   └── api-reference.md                  # Documentación detallada de la API
├── scripts/
│   ├── seed_db.py                        # Carga de datos de prueba
│   └── reset_db.py                       # Reseteo de base de datos
├── tests/
│   └── conftest.py                       # Fixtures (SQLite in-memory)
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```env
# --- Base de datos ---
DATABASE_URL=postgresql://usuario:password@localhost:5432/utcubamba_db

# --- JWT ---
SECRET_KEY=clave-secreta-muy-larga-y-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# --- Entorno ---
ENVIRONMENT=development

# --- CORS ---
FRONTEND_URL=http://localhost:9002
CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002

# --- Contacto ---
CONTACT_EMAIL=soporte@utcubamba.com

# --- Redis (Celery) ---
REDIS_URL=redis://localhost:6379/0

# --- Mailtrap (password reset) ---
MAILTRAP_HOST=sandbox.smtp.mailtrap.io
MAILTRAP_PORT=587
MAILTRAP_USERNAME=
MAILTRAP_PASSWORD=
MAIL_FROM=noreply@utcubamba.com
MAIL_FROM_NAME=Utcubamba API
```

## Cómo levantar el proyecto

### Opción 1 — Local (con Python y PostgreSQL instalados)

```powershell
# 1. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate    # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
Copy-Item .env.example .env
# Editar .env con tus datos

# 4. Ejecutar migraciones
alembic upgrade head

# 5. (Opcional) Cargar datos de prueba
python scripts/seed_db.py

# 6. Levantar el servidor
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 2 — Docker (solo backend + base de datos)

```powershell
docker compose up --build
```

Esto levanta automáticamente PostgreSQL y el backend con las migraciones aplicadas.

> Para levantar el stack completo (backend + frontend), usa el `docker-compose.yml` de la carpeta raíz si tienes ambos repositorios clonados juntos.

## Documentación de la API

### Documentación interactiva (con el servidor corriendo)

| Interfaz | URL |
|---|---|
| Swagger UI | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |
| OpenAPI JSON | http://localhost:8000/api/openapi.json |

### Documentación estática

Consulta [`docs/api-reference.md`](docs/api-reference.md) para una referencia completa
de todos los endpoints, modelos de datos, códigos de error y ejemplos.

## Ejecutar pruebas

```powershell
pytest tests/
```

Los tests usan SQLite in-memory (no requieren PostgreSQL).

## Excepciones de dominio

Los servicios lanzan excepciones de dominio (`src/exceptions.py`) en lugar de
`HTTPException` de FastAPI. El handler global en `main.py` las convierte automáticamente
a respuestas HTTP:

| Excepción | HTTP |
|---|---|
| `NotFoundError` y subclases | 404 |
| `ForbiddenError` | 403 |
| `ValidationError` | 400 |
| `DomainError` (genérico) | 500 |

## Tareas Celery

Las tareas programadas se definen en `src/tasks/tasks.py`:

- `batch_predict_all()` — predicción masiva para todos los medicamentos
- `check_low_stock_alerts()` — alertas de stock bajo
- `cleanup_old_data()` — limpieza de datos antiguos
- `send_scheduled_reports()` — envío programado de reportes

Requieren un worker Celery corriendo:
```powershell
celery -A src.tasks.celery_app worker --loglevel=info
```

## Proyecto relacionado

- **Frontend:** [Utcubamba-project](https://github.com/vtorresm/Utcubamba-project) — interfaz en Next.js que consume esta API
