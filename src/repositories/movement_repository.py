"""
Repositorio concreto para el modelo Movement.

Encapsula las consultas de movimientos de inventario y
provee la serie de tiempo de consumo diario que alimenta
a los modelos de forecasting.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from sqlmodel import Session, select

from src.models.movement import Movement, MovementType
from .base import BaseRepository


class MovementRepository(BaseRepository[Movement]):
    """
    Repositorio de movimientos de inventario.

    Provee operaciones CRUD estándar (heredadas) y la consulta
    especializada `get_consumption_series` que agrega los movimientos
    OUT en una serie de tiempo diaria, requerida por ARIMA y Prophet.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(Movement, db)

    # ── Consultas específicas ───────────────────────────────────────────────

    def get_consumption_series(
        self,
        medication_id: int,
        months_back: int = 24,
        freq: str = "D",
    ) -> pd.Series:
        """
        Devuelve la serie de consumo diario (movimientos OUT) del medicamento.

        La serie está indexada por fecha (DatetimeIndex), rellenada con ceros
        en los días sin movimientos, y opcionalmente re-muestreada a `freq`.

        Parameters
        ----------
        medication_id : int
            ID del medicamento a consultar.
        months_back : int
            Número de meses hacia atrás a recuperar (default 24).
        freq : str
            Frecuencia de la serie: "D" diaria, "W" semanal, "ME" mensual.

        Returns
        -------
        pd.Series
            Serie de Pandas con el consumo agregado; vacía si no hay datos.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30 * months_back)

        stmt = select(Movement).where(
            Movement.medication_id == medication_id,
            Movement.type == MovementType.OUT,
            Movement.date >= start_date,
            Movement.date <= end_date,
        )
        movements = self._db.exec(stmt).all()

        if not movements:
            return pd.Series(dtype=float)

        df = pd.DataFrame(
            [{"date": m.date.date(), "quantity": m.quantity} for m in movements]
        )
        df["date"] = pd.to_datetime(df["date"])
        series = df.groupby("date")["quantity"].sum()

        # Completar fechas faltantes con 0
        full_idx = pd.date_range(
            start=series.index.min(), end=series.index.max(), freq="D"
        )
        series = series.reindex(full_idx, fill_value=0.0)

        if freq != "D":
            series = series.resample(freq).sum()

        return series

    def get_recent_movements(
        self,
        medication_id: int,
        days: int = 30,
    ) -> list:
        """Devuelve los movimientos recientes (IN y OUT) de un medicamento."""
        since = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(Movement)
            .where(
                Movement.medication_id == medication_id,
                Movement.date >= since,
            )
            .order_by(Movement.date.desc())
        )
        return list(self._db.exec(stmt).all())
