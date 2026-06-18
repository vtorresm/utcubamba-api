"""
Repositorio concreto para ForecastRun y ForecastPoint.

Centraliza todas las consultas de forecasting, desacoplando
la lógica de acceso a datos del servicio de predicción.
"""

from __future__ import annotations

from typing import List, Optional

from sqlmodel import Session, select

from src.models.forecast import ForecastPoint, ForecastRun
from .base import BaseRepository


class ForecastRepository(BaseRepository[ForecastRun]):
    """
    Repositorio de ejecuciones de forecast (ForecastRun).

    Además de las operaciones CRUD heredadas, provee consultas
    específicas para recuperar el histórico y el último run.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(ForecastRun, db)

    # ── Consultas específicas ───────────────────────────────────────────────

    def get_latest_for_medication(
        self,
        medication_id: int,
        model_type: Optional[str] = None,
    ) -> Optional[ForecastRun]:
        """Devuelve el ForecastRun más reciente para un medicamento."""
        stmt = (
            select(ForecastRun)
            .where(ForecastRun.medication_id == medication_id)
            .order_by(ForecastRun.created_at.desc())
        )
        if model_type:
            stmt = stmt.where(ForecastRun.model_type == model_type)
        return self._db.exec(stmt).first()

    def get_history_for_medication(
        self,
        medication_id: int,
        limit: int = 10,
        model_type: Optional[str] = None,
    ) -> List[ForecastRun]:
        """Devuelve el historial de ForecastRuns para un medicamento."""
        stmt = (
            select(ForecastRun)
            .where(ForecastRun.medication_id == medication_id)
            .order_by(ForecastRun.created_at.desc())
            .limit(limit)
        )
        if model_type:
            stmt = stmt.where(ForecastRun.model_type == model_type)
        return list(self._db.exec(stmt).all())

    def get_points_for_run(self, run_id: int) -> List[ForecastPoint]:
        """Devuelve los ForecastPoints ordenados por fecha para un run."""
        stmt = (
            select(ForecastPoint)
            .where(ForecastPoint.forecast_run_id == run_id)
            .order_by(ForecastPoint.date)
        )
        return list(self._db.exec(stmt).all())

    def save_run_with_points(
        self,
        run: ForecastRun,
        points: List[ForecastPoint],
    ) -> ForecastRun:
        """
        Persiste un ForecastRun junto con todos sus ForecastPoints
        en una única transacción.
        """
        self._db.add(run)
        self._db.flush()  # obtener run.id antes de los puntos

        for pt in points:
            pt.forecast_run_id = run.id
            self._db.add(pt)

        self._db.commit()
        self._db.refresh(run)
        return run
