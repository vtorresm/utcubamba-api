# Utcubamba API

API para predecir desabastecimientos de medicamentos usando Random Forest.

## Configuración

1. Crea un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt

3. Inicializa la base de datos:
   ```bash
   python scripts/seed_db.py

4. Inicia el servidor:
   ```bash
   uvicorn src.main:app --reload