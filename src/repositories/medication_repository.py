"""
Repositorio concreto para el modelo Medication.

Encapsula todas las consultas relacionadas con medicamentos,
manteniendo la lógica de acceso a datos fuera de los servicios.
"""

from __future__ import annotations

from typing import List, Optional, Set

from sqlmodel import Session, select

from src.models.medication import Medication
from .base import BaseRepository


class MedicationRepository(BaseRepository[Medication]):
    """
    Repositorio de medicamentos.

    Hereda las operaciones CRUD de BaseRepository y agrega
    consultas específicas del dominio de medicamentos.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(Medication, db)

    # ── Consultas específicas ───────────────────────────────────────────────

    def get_by_name(self, name: str) -> Optional[Medication]:
        """Busca un medicamento por nombre exacto (case-insensitive)."""
        stmt = select(Medication).where(Medication.name.ilike(name))
        return self._db.exec(stmt).first()

    def get_all_ids(self) -> Set[int]:
        """Devuelve el conjunto de IDs de todos los medicamentos existentes."""
        rows = self._db.exec(select(Medication.id)).all()
        return {r for r in rows if r is not None}

    def get_low_stock(self) -> List[Medication]:
        """Devuelve medicamentos con stock ≤ min_stock."""
        stmt = select(Medication).where(Medication.stock <= Medication.min_stock)
        return list(self._db.exec(stmt).all())

    def get_active(self, skip: int = 0, limit: int = 200) -> List[Medication]:
        """Devuelve medicamentos con estado 'Activo'."""
        stmt = (
            select(Medication)
            .where(Medication.status == "Activo")
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.exec(stmt).all())
