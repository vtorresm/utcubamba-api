from fastapi import APIRouter, Depends, HTTPException, status, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from typing import List, Optional
from src.db.database import get_db
from src.models.schemas import Medicamento, MedicamentoCreate
from src.models.database_models import Medicamento as MedicamentoModel
from src.api.dependencies import get_current_user, require_role
import logging
import csv
import io
from datetime import date, datetime
import pandas as pd

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Medicamento)
def create_medicamento(medicamento: MedicamentoCreate, current_user: MedicamentoModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to create medicamento: {medicamento.nombre_comercial}")
    db_medicamento = MedicamentoModel(**medicamento.dict())
    db.add(db_medicamento)
    try:
        db.commit()
        db.refresh(db_medicamento)
        logger.info(f"Medicamento created successfully: {medicamento.nombre_comercial}")
        return db_medicamento
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to create medicamento: Barcode {medicamento.codigo_barras} already exists")
        raise HTTPException(status_code=400, detail="Barcode already exists")

@router.get("/", response_model=List[Medicamento])
def read_medicamentos(
    skip: int = 0,
    limit: int = 100,
    nombre_comercial: Optional[str] = None,
    nombre_generico: Optional[str] = None,
    presentacion: Optional[str] = None,
    laboratorio: Optional[str] = None,
    requiere_receta: Optional[bool] = None,
    stock_min: Optional[int] = None,
    stock_max: Optional[int] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    fecha_vencimiento_antes: Optional[date] = None,
    fecha_vencimiento_despues: Optional[date] = None,
    current_user: MedicamentoModel = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    logger.info(f"Listing medicamentos (skip={skip}, limit={limit}) by admin: {current_user.email}")
    query = db.query(MedicamentoModel)

    # Aplicar filtros
    filters = []
    if nombre_comercial:
        filters.append(MedicamentoModel.nombre_comercial.ilike(f"%{nombre_comercial}%"))
    if nombre_generico:
        filters.append(MedicamentoModel.nombre_generico.ilike(f"%{nombre_generico}%"))
    if presentacion:
        filters.append(MedicamentoModel.presentacion.ilike(f"%{presentacion}%"))
    if laboratorio:
        filters.append(MedicamentoModel.laboratorio.ilike(f"%{laboratorio}%"))
    if requiere_receta is not None:
        filters.append(MedicamentoModel.requiere_receta == requiere_receta)
    if stock_min is not None:
        filters.append(MedicamentoModel.stock_actual >= stock_min)
    if stock_max is not None:
        filters.append(MedicamentoModel.stock_actual <= stock_max)
    if precio_min is not None:
        filters.append(MedicamentoModel.precio_unitario >= precio_min)
    if precio_max is not None:
        filters.append(MedicamentoModel.precio_unitario <= precio_max)
    if fecha_vencimiento_antes:
        filters.append(MedicamentoModel.fecha_vencimiento <= fecha_vencimiento_antes)
    if fecha_vencimiento_despues:
        filters.append(MedicamentoModel.fecha_vencimiento >= fecha_vencimiento_despues)

    if filters:
        query = query.filter(and_(*filters))

    medicamentos = query.offset(skip).limit(limit).all()
    logger.debug(f"Retrieved {len(medicamentos)} medicamentos with filters: {filters}")
    return medicamentos

@router.get("/{medicamento_id}", response_model=Medicamento)
def read_medicamento(medicamento_id: int, current_user: MedicamentoModel = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Fetching medicamento ID: {medicamento_id} by user: {current_user.email}")
    medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == medicamento_id).first()
    if not medicamento:
        logger.error(f"Medicamento ID: {medicamento_id} not found")
        raise HTTPException(status_code=404, detail="Medicamento not found")
    logger.debug(f"Medicamento retrieved: {medicamento.nombre_comercial}")
    return medicamento

@router.put("/{medicamento_id}", response_model=Medicamento)
def update_medicamento(medicamento_id: int, medicamento: MedicamentoCreate, current_user: MedicamentoModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to update medicamento ID: {medicamento_id} by admin: {current_user.email}")
    db_medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == medicamento_id).first()
    if not db_medicamento:
        logger.error(f"Medicamento ID: {medicamento_id} not found for update")
        raise HTTPException(status_code=404, detail="Medicamento not found")
    
    for key, value in medicamento.dict().items():
        setattr(db_medicamento, key, value)
    
    try:
        db.commit()
        db.refresh(db_medicamento)
        logger.info(f"Medicamento updated successfully: {db_medicamento.nombre_comercial}")
        return db_medicamento
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to update medicamento: Barcode {medicamento.codigo_barras} already exists")
        raise HTTPException(status_code=400, detail="Barcode already exists")

@router.delete("/{medicamento_id}")
def delete_medicamento(medicamento_id: int, current_user: MedicamentoModel = Depends(require_role("admin")), db: Session = Depends(get_db)):
    logger.info(f"Attempting to delete medicamento ID: {medicamento_id} by admin: {current_user.email}")
    medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.medicamento_id == medicamento_id).first()
    if not medicamento:
        logger.error(f"Medicamento ID: {medicamento_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Medicamento not found")
    db.delete(medicamento)
    db.commit()
    logger.info(f"Medicamento deleted successfully: {medicamento.nombre_comercial}")
    return {"message": "Medicamento deleted successfully"}

@router.get("/export/csv")
def export_medicamentos_csv(
    nombre_comercial: Optional[str] = None,
    nombre_generico: Optional[str] = None,
    presentacion: Optional[str] = None,
    laboratorio: Optional[str] = None,
    requiere_receta: Optional[bool] = None,
    stock_min: Optional[int] = None,
    stock_max: Optional[int] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    fecha_vencimiento_antes: Optional[date] = None,
    fecha_vencimiento_despues: Optional[date] = None,
    current_user: MedicamentoModel = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    logger.info(f"Exporting medicamentos to CSV by admin: {current_user.email}")
    query = db.query(MedicamentoModel)

    # Aplicar los mismos filtros que en read_medicamentos
    filters = []
    if nombre_comercial:
        filters.append(MedicamentoModel.nombre_comercial.ilike(f"%{nombre_comercial}%"))
    if nombre_generico:
        filters.append(MedicamentoModel.nombre_generico.ilike(f"%{nombre_generico}%"))
    if presentacion:
        filters.append(MedicamentoModel.presentacion.ilike(f"%{presentacion}%"))
    if laboratorio:
        filters.append(MedicamentoModel.laboratorio.ilike(f"%{laboratorio}%"))
    if requiere_receta is not None:
        filters.append(MedicamentoModel.requiere_receta == requiere_receta)
    if stock_min is not None:
        filters.append(MedicamentoModel.stock_actual >= stock_min)
    if stock_max is not None:
        filters.append(MedicamentoModel.stock_actual <= stock_max)
    if precio_min is not None:
        filters.append(MedicamentoModel.precio_unitario >= precio_min)
    if precio_max is not None:
        filters.append(MedicamentoModel.precio_unitario <= precio_max)
    if fecha_vencimiento_antes:
        filters.append(MedicamentoModel.fecha_vencimiento <= fecha_vencimiento_antes)
    if fecha_vencimiento_despues:
        filters.append(MedicamentoModel.fecha_vencimiento >= fecha_vencimiento_despues)

    if filters:
        query = query.filter(and_(*filters))

    medicamentos = query.all()
    logger.debug(f"Exporting {len(medicamentos)} medicamentos to CSV")

    # Crear el CSV en memoria
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "medicamento_id", "nombre_comercial", "nombre_generico", "presentacion",
            "concentracion", "laboratorio", "precio_unitario", "stock_actual",
            "fecha_vencimiento", "codigo_barras", "requiere_receta", "unidad_empaque",
            "via_administracion"
        ]
    )
    writer.writeheader()
    for med in medicamentos:
        writer.writerow({
            "medicamento_id": med.medicamento_id,
            "nombre_comercial": med.nombre_comercial,
            "nombre_generico": med.nombre_generico,
            "presentacion": med.presentacion,
            "concentracion": med.concentracion,
            "laboratorio": med.laboratorio,
            "precio_unitario": float(med.precio_unitario),
            "stock_actual": med.stock_actual,
            "fecha_vencimiento": med.fecha_vencimiento.isoformat(),
            "codigo_barras": med.codigo_barras,
            "requiere_receta": med.requiere_receta,
            "unidad_empaque": med.unidad_empaque,
            "via_administracion": med.via_administracion
        })

    # Configurar la respuesta de streaming
    headers = {
        "Content-Disposition": "attachment; filename=medicamentos.csv",
        "Content-Type": "text/csv",
    }
    logger.info("Medicamentos exported to CSV successfully")
    return StreamingResponse(
        iter([output.getvalue()]),
        headers=headers,
        media_type="text/csv"
    )

def validate_medicamento_data(row, row_num, expected_headers, db: Session):
    errors = []
    
    # Verificar unicidad de codigo_barras
    codigo_barras = str(row.get("codigo_barras", "")).strip() if row.get("codigo_barras") else None
    if codigo_barras:
        existing_medicamento = db.query(MedicamentoModel).filter(MedicamentoModel.codigo_barras == codigo_barras).first()
        if existing_medicamento:
            logger.error(f"Validation error in row {row_num}: Barcode {codigo_barras} already exists")
            errors.append(f"Row {row_num}: Barcode {codigo_barras} already exists")
            return False, errors

    try:
        # Convertir y validar datos
        medicamento_data = {
            "nombre_comercial": str(row["nombre_comercial"]).strip() if row.get("nombre_comercial") else "",
            "nombre_generico": str(row["nombre_generico"]).strip() if row.get("nombre_generico") else "",
            "presentacion": str(row["presentacion"]).strip() if row.get("presentacion") else "",
            "concentracion": str(row["concentracion"]).strip() if row.get("concentracion") else "",
            "laboratorio": str(row["laboratorio"]).strip() if row.get("laboratorio") else "",
            "precio_unitario": float(row["precio_unitario"]) if row.get("precio_unitario") else None,
            "stock_actual": int(row["stock_actual"]) if row.get("stock_actual") else None,
            "fecha_vencimiento": pd.to_datetime(row["fecha_vencimiento"]).date() if row.get("fecha_vencimiento") else None,
            "codigo_barras": codigo_barras,
            "requiere_receta": str(row["requiere_receta"]).lower() in ("true", "1", "yes") if row.get("requiere_receta") else False,
            "unidad_empaque": int(row["unidad_empaque"]) if row.get("unidad_empaque") else None,
            "via_administracion": str(row["via_administracion"]).strip() if row.get("via_administracion") else ""
        }

        # Validar con Pydantic
        MedicamentoCreate(**medicamento_data)
        return True, []

    except ValueError as ve:
        logger.error(f"Validation error in row {row_num}: {str(ve)}")
        errors.append(f"Row {row_num}: {str(ve)}")
    except Exception as e:
        logger.error(f"Unexpected error in row {row_num}: {str(e)}")
        errors.append(f"Row {row_num}: {str(e)}")
    
    return False, errors

@router.post("/import")
async def import_medicamentos(
    file: UploadFile = File(...),
    current_user: MedicamentoModel = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    logger.info(f"Starting file import by admin: {current_user.email}")
    
    # Verificar tipo de archivo
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        logger.error("Invalid file format: File must be CSV or Excel")
        raise HTTPException(status_code=400, detail="File must be CSV or Excel (.csv, .xlsx, .xls)")

    # Leer el contenido del archivo
    content = await file.read()
    expected_headers = [
        "medicamento_id", "nombre_comercial", "nombre_generico", "presentacion",
        "concentracion", "laboratorio", "precio_unitario", "stock_actual",
        "fecha_vencimiento", "codigo_barras", "requiere_receta", "unidad_empaque",
        "via_administracion"
    ]

    rows = []
    if filename.endswith('.csv'):
        csv_file = io.StringIO(content.decode('utf-8'))
        reader = csv.DictReader(csv_file)
        if not all(header in reader.fieldnames for header in expected_headers):
            missing = [h for h in expected_headers if h not in reader.fieldnames]
            logger.error(f"Missing required headers in CSV: {missing}")
            raise HTTPException(status_code=400, detail=f"Missing required headers: {missing}")
        rows = list(reader)
    else:  # Excel
        try:
            df = pd.read_excel(io.BytesIO(content))
            if not all(header in df.columns for header in expected_headers):
                missing = [h for h in expected_headers if h not in df.columns]
                logger.error(f"Missing required headers in Excel: {missing}")
                raise HTTPException(status_code=400, detail=f"Missing required headers: {missing}")
            rows = df.to_dict('records')
        except Exception as e:
            logger.error(f"Failed to read Excel file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")

    imported_count = 0
    errors = []

    for row_num, row in enumerate(rows, start=2):  # start=2 para contar la línea de datos
        try:
            # Convertir y validar datos
            medicamento_data = {
                "nombre_comercial": str(row["nombre_comercial"]).strip() if row.get("nombre_comercial") else "",
                "nombre_generico": str(row["nombre_generico"]).strip() if row.get("nombre_generico") else "",
                "presentacion": str(row["presentacion"]).strip() if row.get("presentacion") else "",
                "concentracion": str(row["concentracion"]).strip() if row.get("concentracion") else "",
                "laboratorio": str(row["laboratorio"]).strip() if row.get("laboratorio") else "",
                "precio_unitario": float(row["precio_unitario"]) if row.get("precio_unitario") else None,
                "stock_actual": int(row["stock_actual"]) if row.get("stock_actual") else None,
                "fecha_vencimiento": pd.to_datetime(row["fecha_vencimiento"]).date() if row.get("fecha_vencimiento") else None,
                "codigo_barras": str(row["codigo_barras"]).strip() if row.get("codigo_barras") and str(row["codigo_barras"]).strip() else None,
                "requiere_receta": str(row["requiere_receta"]).lower() in ("true", "1", "yes") if row.get("requiere_receta") else False,
                "unidad_empaque": int(row["unidad_empaque"]) if row.get("unidad_empaque") else None,
                "via_administracion": str(row["via_administracion"]).strip() if row.get("via_administracion") else ""
            }

            # Validar con Pydantic
            medicamento = MedicamentoCreate(**medicamento_data)

            # Crear registro en la base de datos
            db_medicamento = MedicamentoModel(**medicamento.dict())
            db.add(db_medicamento)
            db.commit()
            db.refresh(db_medicamento)
            imported_count += 1
            logger.info(f"Imported medicamento: {medicamento.nombre_comercial} (row {row_num})")

        except ValueError as ve:
            logger.error(f"Validation error in row {row_num}: {str(ve)}")
            errors.append(f"Row {row_num}: {str(ve)}")
        except IntegrityError as ie:
            db.rollback()
            logger.error(f"Database error in row {row_num}: Barcode {row.get('codigo_barras')} already exists")
            errors.append(f"Row {row_num}: Barcode {row.get('codigo_barras')} already exists")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error in row {row_num}: {str(e)}")
            errors.append(f"Row {row_num}: {str(e)}")

    logger.info(f"File import completed: {imported_count} medicamentos imported, {len(errors)} errors")
    if errors:
        return {
            "message": f"Imported {imported_count} medicamentos with {len(errors)} errors",
            "errors": errors
        }
    return {"message": f"Successfully imported {imported_count} medicamentos"}

@router.post("/validate")
async def validate_medicamentos(
    file: UploadFile = File(...),
    current_user: MedicamentoModel = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    logger.info(f"Starting file validation by admin: {current_user.email}, file: {file.filename}")
    
    # Verificar tipo de archivo
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        logger.error("Invalid file format: File must be CSV or Excel (.csv, .xlsx, .xls)")
        raise HTTPException(status_code=400, detail="File must be CSV or Excel (.csv, .xlsx, .xls)")

    # Leer el contenido del archivo
    content = await file.read()
    expected_headers = [
        "medicamento_id", "nombre_comercial", "nombre_generico", "presentacion",
        "concentracion", "laboratorio", "precio_unitario", "stock_actual",
        "fecha_vencimiento", "codigo_barras", "requiere_receta", "unidad_empaque",
        "via_administracion"
    ]

    rows = []
    file_type = "CSV" if filename.endswith('.csv') else "Excel"
    logger.debug(f"Processing {file_type} file: {filename}")

    try:
        if filename.endswith('.csv'):
            csv_file = io.StringIO(content.decode('utf-8'))
            reader = csv.DictReader(csv_file)
            if not all(header in reader.fieldnames for header in expected_headers):
                missing = [h for h in expected_headers if h not in reader.fieldnames]
                logger.error(f"Missing required headers in CSV: {missing}")
                raise HTTPException(status_code=400, detail=f"Missing required headers: {missing}")
            rows = list(reader)
        else:  # Excel
            df = pd.read_excel(io.BytesIO(content))
            if not all(header in df.columns for header in expected_headers):
                missing = [h for h in expected_headers if h not in df.columns]
                logger.error(f"Missing required headers in Excel: {missing}")
                raise HTTPException(status_code=400, detail=f"Missing required headers: {missing}")
            rows = df.to_dict('records')
    except Exception as e:
        logger.error(f"Failed to read {file_type} file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to read {file_type} file: {str(e)}")

    valid_count = 0
    errors = []

    for row_num, row in enumerate(rows, start=2):  # start=2 para contar la línea de datos
        is_valid, row_errors = validate_medicamento_data(row, row_num, expected_headers, db)
        if is_valid:
            valid_count += 1
        errors.extend(row_errors)

    logger.info(f"{file_type} validation completed: {valid_count} valid rows, {len(errors)} errors")
    if errors:
        return {
            "message": f"Validated {valid_count} valid rows with {len(errors)} errors",
            "errors": errors
        }
    return {"message": f"Successfully validated {valid_count} rows"}