# Utcubamba API

API para la gestión de usuarios, medicamentos y predicción de desabastecimientos en el sistema de farmacia de la UTC.

## Características Principales

- 🔐 Autenticación JWT
- 👥 Gestión de usuarios con roles
- 💊 Gestión de inventario de medicamentos
- 📊 Predicción de desabastecimientos usando Random Forest
- 📚 Documentación completa de la API

## Documentación de la API

### Documentación Técnica

- [Autenticación](./docs/api/AUTHENTICATION.md) - Gestión de usuarios y autenticación
- [Usuarios](./docs/api/USERS.md) - Gestión de perfiles de usuario
- [Medicamentos](./docs/api/MEDICATIONS.md) - Gestión del inventario de medicamentos
- [Predicciones](./docs/api/PREDICTIONS.md) - Predicción y análisis de desabastecimientos

### Documentación Interactiva

Después de iniciar el servidor, accede a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Configuración Rápida

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/utcubamba-api.git
   cd utcubamba-api
   ```

2. **Configurar entorno virtual**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

5. **Inicializar la base de datos**
   ```bash
   python scripts/seed_db.py
   ```

6. **Iniciar el servidor de desarrollo**
   ```bash
   uvicorn src.main:app --reload
   ```

## Estructura del Proyecto

```
utcubamba-api/
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py       # Autenticación
│   │       │   ├── users.py      # Gestión de usuarios
│   │       │   ├── medications.py # Gestión de medicamentos
│   │       │   └── predictions.py # Predicciones
│   │       └── __init__.py
│   ├── core/                     # Configuraciones centrales
│   ├── models/                   # Modelos de base de datos
│   └── services/                 # Lógica de negocio
├── scripts/                      # Scripts de utilidad
├── tests/                        # Pruebas unitarias
├── .env.example                  # Ejemplo de variables de entorno
├── requirements.txt              # Dependencias
└── README.md                     # Este archivo
```

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```
# Configuración de la base de datos
DATABASE_URL=sqlite:///./utcubamba.db

# Configuración de autenticación
SECRET_KEY=tu_clave_secreta_muy_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de correo (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=tu_correo@utcubamba.edu.pe
EMAIL_PASSWORD=tu_contraseña
```

## Ejecutando las Pruebas

```bash
pytest tests/
```

## Despliegue

### Requisitos
- Python 3.8+
- Base de datos PostgreSQL
- Servidor web (Nginx, Apache, etc.)

### Pasos
1. Configurar variables de entorno de producción
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar migraciones
4. Configurar servidor web
5. Iniciar la aplicación con un servidor ASGI como uvicorn o gunicorn

## Contribución

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Haz push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.

## Contacto

Para soporte o consultas, contacta al equipo de desarrollo en:
- Email: desarrollo@utcubamba.edu.pe
- Sitio web: [www.utcubamba.edu.pe](https://www.utcubamba.edu.pe)