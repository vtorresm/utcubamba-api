"""
Endpoint para carga masiva de datos históricos de consumo de medicamentos.

Formato esperado del CSV/XLSX:
  Columnas requeridas : medication_id, date, real_usage, stock
  Columnas opcionales : predicted_usage, month_of_year, regional_demand

Ejemplo de fila:
  medication_id | date       | real_usage | stock | predicted_usage | regional_demand
  1             | 2025-01-15 | 23.5       | 150   | 25.0            | 0.0
"""

from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.dependencies.auth import get_current_user
from src.models.medication import Medication
from src.models.prediction import Prediction
from src.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Persistencia de historial en JSON ──────────────────────────────────────────
# Se guarda en /tmp para no necesitar migración de BD.
_HISTORY_FILE = os.environ.get("UPLOAD_HISTORY_FILE", "/tmp/upload_history.json")


def _load_history() -> list:
    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_history(records: list) -> None:
    try:
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, default=str)
    except Exception as e:
        logger.warning("No se pudo guardar historial de uploads: %s", e)


# ── Modelos de respuesta ───────────────────────────────────────────────────────

class UploadError(BaseModel):
    row: int
    reason: str


class UploadResult(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    total_rows: int
    inserted: int
    skipped: int
    errors: List[UploadError]


class UploadHistoryItem(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    total_rows: int
    inserted: int
    skipped: int
    status: str  # "completed" | "partial" | "error"


# ── Constantes ─────────────────────────────────────────────────────────────────
REQUIRED_COLS = {"medication_id", "date", "real_usage", "stock"}
MAX_ROWS = 50_000


# ── Helper: parsear archivo ────────────────────────────────────────────────────

def _parse_file(upload: UploadFile) -> pd.DataFrame:
    content = upload.file.read()
    name = (upload.filename or "").lower()

    if name.endswith(".csv"):
        try:
            return pd.read_csv(io.BytesIO(content))
        except Exception as exc:
            raise HTTPException(400, f"No se pudo leer el CSV: {exc}")

    if name.endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(io.BytesIO(content), engine="openpyxl")
        except Exception as exc:
            raise HTTPException(400, f"No se pudo leer el Excel: {exc}")

    raise HTTPException(400, "Formato no soportado. Usa .csv o .xlsx")


# ── Endpoint: subir archivo ────────────────────────────────────────────────────

@router.post(
    "/upload-historico/",
    response_model=UploadResult,
    summary="Cargar datos históricos de consumo",
    description="""
Sube un archivo CSV o XLSX con registros históricos de consumo de medicamentos.

**Columnas requeridas:** `medication_id`, `date`, `real_usage`, `stock`
**Columnas opcionales:** `predicted_usage`, `month_of_year`, `regional_demand`

Las filas con `medication_id` inexistente o datos inválidos se omiten y se reportan en `errors`.
""",
)
async def upload_historical(
    file: UploadFile = File(..., description="Archivo CSV o XLSX"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResult:
    # ── 1. Parsear ─────────────────────────────────────────────────────────────
    df = _parse_file(file)

    # Normalizar nombres de columna (strip + lowercase)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise HTTPException(
            400,
            f"Faltan columnas requeridas: {', '.join(sorted(missing))}. "
            f"Columnas encontradas: {', '.join(df.columns)}",
        )

    if len(df) > MAX_ROWS:
        raise HTTPException(400, f"El archivo supera el límite de {MAX_ROWS} filas.")

    # ── 2. Pre-cargar IDs de medicamentos válidos ──────────────────────────────
    valid_med_ids: set[int] = {
        m.id for m in db.query(Medication.id).all()  # type: ignore[attr-defined]
    }

    # ── 3. Procesar fila por fila ──────────────────────────────────────────────
    errors: list[UploadError] = []
    to_insert: list[Prediction] = []

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # +2: encabezado + índice 0-based

        try:
            med_id = int(row["medication_id"])
            if med_id not in valid_med_ids:
                errors.append(UploadError(row=row_num, reason=f"medication_id={med_id} no existe"))
                continue

            # Parsear fecha
            raw_date = row["date"]
            if isinstance(raw_date, str):
                date_val = datetime.fromisoformat(raw_date.strip())
            elif isinstance(raw_date, (datetime,)):
                date_val = raw_date
            elif hasattr(raw_date, "to_pydatetime"):
                date_val = raw_date.to_pydatetime()
            else:
                date_val = datetime.fromisoformat(str(raw_date))

            real_usage = float(row["real_usage"])
            if real_usage < 0:
                errors.append(UploadError(row=row_num, reason="real_usage no puede ser negativo"))
                continue

            stock_val = float(row["stock"])
            if stock_val < 0:
                errors.append(UploadError(row=row_num, reason="stock no puede ser negativo"))
                continue

            predicted_usage = float(row.get("predicted_usage", real_usage) or real_usage)
            month_of_year = int(row.get("month_of_year", date_val.month) or date_val.month)
            regional_demand = float(row.get("regional_demand", 0.0) or 0.0)

            to_insert.append(Prediction(
                medication_id=med_id,
                date=date_val,
                real_usage=real_usage,
                predicted_usage=max(predicted_usage, 0.001),  # campo gt=0
                stock=stock_val,
                month_of_year=month_of_year,
                regional_demand=regional_demand,
                shortage=stock_val == 0,
                probability=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ))

        except Exception as exc:
            errors.append(UploadError(row=row_num, reason=str(exc)))

    # ── 4. Bulk insert ─────────────────────────────────────────────────────────
    inserted = 0
    if to_insert:
        try:
            db.bulk_save_objects(to_insert)
            db.commit()
            inserted = len(to_insert)
        except Exception as exc:
            db.rollback()
            logger.error("Error en bulk insert: %s", exc, exc_info=True)
            raise HTTPException(500, f"Error al guardar en base de datos: {exc}")

    # ── 5. Guardar en historial ────────────────────────────────────────────────
    upload_id = f"upload_{int(datetime.utcnow().timestamp() * 1000)}"
    uploaded_at = datetime.utcnow().isoformat()
    record_status = (
        "completed" if not errors
        else "partial" if inserted > 0
        else "error"
    )

    history = _load_history()
    history.insert(0, {
        "id": upload_id,
        "filename": file.filename or "archivo",
        "uploaded_at": uploaded_at,
        "total_rows": len(df),
        "inserted": inserted,
        "skipped": len(errors),
        "status": record_status,
    })
    _save_history(history)

    return UploadResult(
        id=upload_id,
        filename=file.filename or "archivo",
        uploaded_at=uploaded_at,
        total_rows=len(df),
        inserted=inserted,
        skipped=len(errors),
        errors=errors[:50],  # máximo 50 errores en la respuesta
    )


# ── Endpoint: historial de cargas ──────────────────────────────────────────────

@router.get(
    "/uploads/",
    response_model=List[UploadHistoryItem],
    summary="Historial de cargas de datos históricos",
)
async def list_uploads(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
) -> List[UploadHistoryItem]:
    history = _load_history()
    return [UploadHistoryItem(**h) for h in history[:limit]]
