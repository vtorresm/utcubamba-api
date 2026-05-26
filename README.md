# Utcubamba API

API REST para la gestión de usuarios, medicamentos y predicción de desabastecimientos en el sistema de farmacia de la red de salud Utcubamba.

## Tecnologías

- **Python 3.12+**
- **FastAPI** — framework web
- **SQLModel** — ORM sobre SQLAlchemy
- **PostgreSQL** — base de datos
- **Alembic** — migraciones
- **JWT** — autenticación
- **Scikit-learn** — modelo de predicción (Random Forest)
- **Uvicorn** — servidor ASGI

## Características

- Autenticación y autorización con JWT
- Gestión de usuarios con roles
- Gestión de inventario de medicamentos y categorías
- Predicción de desabastecimientos con Random Forest
- Documentación interactiva con Swagger y ReDoc
- Rate limiting
- CORS configurado para el frontend

## Estructura del proyecto

```
utcubamba-api/
├── src/
│   ├── api/v1/
│   │   └── endpoints/
│   │       ├── auth.py               # Login y registro
│   │       ├── users.py              # Gestión de usuarios
│   │       ├── medications.py        # Inventario de medicamentos
│   │       ├── categories.py         # Categorías de medicamentos
│   │       ├── predictions.py        # Predicciones de desabastecimiento
│   │       └── prediction_metrics.py # Métricas del modelo
│   ├── core/                         # Configuración, DB, seguridad
│   ├── models/                       # Modelos de base de datos
│   ├── schemas/                      # Esquemas Pydantic
│   ├── services/                     # Lógica de negocio
│   └── main.py                       # Punto de entrada
├── alembic/                          # Migraciones de base de datos
├── scripts/
│   ├── seed_db.py                    # Carga de datos de prueba
│   └── reset_db.py                   # Reseteo de base de datos
├── tests/                            # Pruebas
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/utcubamba_db
SECRET_KEY=clave-secreta-muy-larga-y-segura
ENVIRONMENT=development
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:9002
CORS_ORIGINS=http://localhost:9002,http://127.0.0.1:9002
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

Con el servidor corriendo, accede a:

| Interfaz | URL |
|---|---|
| Swagger UI | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |
| OpenAPI JSON | http://localhost:8000/api/openapi.json |

## Ejecutar pruebas

```powershell
pytest tests/
```

## Proyecto relacionado

- **Frontend:** [Utcubamba-project](https://github.com/vtorresm/Utcubamba-project) — interfaz en Next.js que consume esta API
