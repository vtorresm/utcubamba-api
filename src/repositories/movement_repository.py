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

    Provee operaciones CRUD estandar (heredadas) y la consulta
    especializada get_consumption_series que agrega los movimientos
    OUT en una serie de tiempo diaria, requerida por ARIMA y Prophet.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(Movement, db)

    def get_consumption_series(
        self,
        medication_id: int,
        months_back: int = 24,
        freq: str = "D",
    ) -> pd.Series:
        """
        Devuelve la serie de consumo del medicamento lista para forecasting.

        Cuando los movimientos se registran con granularidad mensual (tipico
        en datos de seed o sistemas legacy), el 96%+ de dias quedarian en 0,
        lo que hace imposible el forecasting. En ese caso se redistribuye
        el total mensual uniformemente entre los dias del mes (estandar en
        gestion de inventario farmaceutico).

        Parameters
        ----------
        medication_id : int
        months_back : int
        freq : str  "D" diaria, "W" semanal, "ME" mensual

        Returns
        -------
        pd.Series con DatetimeIndex
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

        full_idx = pd.date_range(
            start=series.index.min(), end=series.index.max(), freq="D"
        )
        series = series.reindex(full_idx, fill_value=0.0)

        # Deteccion de granularidad mensual
        # Si menos del 15% de dias tienen datos, redistribuir mensual -> diario
        nonzero_count = int((series > 0).sum())
        nonzero_pct = nonzero_count / max(len(series), 1)

        if nonzero_pct < 0.15 and nonzero_count >= 3:
            monthly = series.resample("ME").sum()
            dates_list = []
            rates_list = []
            for month_end, total in monthly.items():
                if total <= 0:
                    continue
                month_start = month_end.replace(day=1)
                days_in_month = month_end.day
                daily_rate = total / days_in_month
                for d in range(days_in_month):
                    day = month_start + pd.Timedelta(days=d)
                    if series.index.min() <= day <= series.index.max():
                        dates_list.append(day)
                        rates_list.append(daily_rate)
            if dates_list:
                smooth = pd.Series(rates_list, index=pd.DatetimeIndex(dates_list))
                series = smooth.reindex(full_idx, fill_value=0.0)

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
