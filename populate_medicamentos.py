import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from sqlalchemy.orm import Session
from datetime import date
from src.db.database import SessionLocal
from src.models.database_models import Medicamento
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def populate_medicamentos():
    logger.info("Starting population of medicamentos table")
    medicamentos = [
        {
            "nombre_comercial": "Panadol",
            "nombre_generico": "Paracetamol",
            "presentacion": "Tabletas",
            "concentracion": "500mg",
            "laboratorio": "Genfar",
            "precio_unitario": 5.50,
            "stock_actual": 150,
            "fecha_vencimiento": date(2026, 3, 15),
            "codigo_barras": "7702031000012",
            "requiere_receta": False,
            "unidad_empaque": 10,
            "via_administracion": "Oral"
        },
        {
            "nombre_comercial": "Ibuprofeno MK",
            "nombre_generico": "Ibuprofeno",
            "presentacion": "Tabletas",
            "concentracion": "400mg",
            "laboratorio": "MK",
            "precio_unitario": 4.20,
            "stock_actual": 200,
            "fecha_vencimiento": date(2027, 1, 10),
            "codigo_barras": "7702031000029",
            "requiere_receta": False,
            "unidad_empaque": 20,
            "via_administracion": "Oral"
        },
        {
            "nombre_comercial": "Amoxicilina Genfar",
            "nombre_generico": "Amoxicilina Trihidrato",
            "presentacion": "Cápsulas",
            "concentracion": "500mg",
            "laboratorio": "Genfar",
            "precio_unitario": 12.75,
            "stock_actual": 80,
            "fecha_vencimiento": date(2026, 11, 30),
            "codigo_barras": "7702031000036",
            "requiere_receta": True,
            "unidad_empaque": 15,
            "via_administracion": "Oral"
        },
        {
            "nombre_comercial": "Loratadina",
            "nombre_generico": "Loratadina",
            "presentacion": "Jarabe",
            "concentracion": "5mg/5ml",
            "laboratorio": "Bayer",
            "precio_unitario": 8.90,
            "stock_actual": 50,
            "fecha_vencimiento": date(2026, 8, 20),
            "codigo_barras": "7702031000043",
            "requiere_receta": False,
            "unidad_empaque": 1,
            "via_administracion": "Oral"
        },
        {
            "nombre_comercial": "Omeprazol",
            "nombre_generico": "Omeprazol",
            "presentacion": "Cápsulas",
            "concentracion": "20mg",
            "laboratorio": "Pfizer",
            "precio_unitario": 15.30,
            "stock_actual": 100,
            "fecha_vencimiento": date(2027, 5, 15),
            "codigo_barras": "7702031000050",
            "requiere_receta": True,
            "unidad_empaque": 14,
            "via_administracion": "Oral"
        },
        {
            "nombre_comercial": "Dolex",
            "nombre_generico": "Paracetamol",
            "presentacion": "Tabletas",
            "concentracion": "650mg",
            "laboratorio": "GSK",
            "precio_unitario": 6.80,
            "stock_actual": 120,
            "fecha_vencimiento": date(2026, 12, 31),
            "codigo_barras": "7702031000067",
            "requiere_receta": False,
            "unidad_empaque": 12,
            "via_administracion": "Oral"
        },
        {
            "nombre_comercial": "Ceftriaxona",
            "nombre_generico": "Ceftriaxona Sódica",
            "presentacion": "Inyectable",
            "concentracion": "1g",
            "laboratorio": "Roche",
            "precio_unitario": 25.00,
            "stock_actual": 30,
            "fecha_vencimiento": date(2026, 9, 10),
            "codigo_barras": "7702031000074",
            "requiere_receta": True,
            "unidad_empaque": 1,
            "via_administracion": "Intravenosa"
        },
        {
            "nombre_comercial": "Salbutamol",
            "nombre_generico": "Salbutamol",
            "presentacion": "Inhalador",
            "concentracion": "100mcg/dosis",
            "laboratorio": "AstraZeneca",
            "precio_unitario": 18.50,
            "stock_actual": 40,
            "fecha_vencimiento": date(2027, 2, 28),
            "codigo_barras": "7702031000081",
            "requiere_receta": True,
            "unidad_empaque": 1,
            "via_administracion": "Inhalatoria"
        },
        {
            "nombre_comercial": "Aspirina",
            "nombre_generico": "Ácido Acetilsalicílico",
            "presentacion": "Tabletas",
            "concentracion": "100mg",
            "laboratorio": "Bayer",
            "precio_unitario": 3.20,
            "stock_actual": 300,
            "fecha_vencimiento": date(2026, 7, 15),
            "codigo_barras": "7702031000098",
            "requiere_receta": False,
            "unidad_empaque": 30,
            "via_administracion": "Oral"
        },
        {
            "nombre_comercial": "Diclofenaco",
            "nombre_generico": "Diclofenaco Sódico",
            "presentacion": "Gel",
            "concentracion": "1%",
            "laboratorio": "Novartis",
            "precio_unitario": 9.75,
            "stock_actual": 60,
            "fecha_vencimiento": date(2026, 10, 5),
            "codigo_barras": "7702031000104",
            "requiere_receta": False,
            "unidad_empaque": 1,
            "via_administracion": "Tópica"
        }
    ]

    db = SessionLocal()
    try:
        for med in medicamentos:
            logger.debug(f"Attempting to insert medicamento: {med['nombre_comercial']}")
            db_medicamento = Medicamento(**med)
            db.add(db_medicamento)
            try:
                db.commit()
                logger.info(f"Inserted medicamento: {med['nombre_comercial']}")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to insert medicamento {med['nombre_comercial']}: {str(e)}")
        logger.info("Medicamentos table populated successfully")
    finally:
        db.close()

if __name__ == "__main__":
    populate_medicamentos()