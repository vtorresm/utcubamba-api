import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Crear el directorio logs/ si no existe
    os.makedirs("logs", exist_ok=True)
    
    # Configurar el logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Nivel por defecto: INFO
    
    # Formato de los logs
    log_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Handler para archivo (rotación para evitar archivos grandes)
    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=10*1024*1024, backupCount=5  # 10MB por archivo, 5 backups
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger