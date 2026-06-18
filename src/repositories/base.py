"""
Patrón Repository — clase base genérica.

BaseRepository[T] define el contrato CRUD estándar que todos los
repositorios concretos deben implementar.  El uso de genéricos
(typing.Generic[T]) garantiza type-safety sin duplicar código.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Type, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(ABC, Generic[T]):
    """
    Repositorio genérico abstracto.

    Proporciona operaciones CRUD básicas sobre cualquier modelo SQLModel.
    Los repositorios concretos extienden esta clase para agregar
    consultas específicas del dominio.

    Parameters
    ----------
    model_class : Type[T]
        La clase del modelo SQLModel que gestiona este repositorio.
    db : Session
        Sesión activa de base de datos (inyectada vía FastAPI Depends).
    """

    def __init__(self, model_class: Type[T], db: Session) -> None:
        self._model = model_class
        self._db = db

    # ── CRUD base ──────────────────────────────────────────────────────────

    def get(self, entity_id: int) -> Optional[T]:
        """Devuelve la entidad por clave primaria, o None si no existe."""
        return self._db.get(self._model, entity_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Devuelve todas las entidades con paginación opcional."""
        stmt = select(self._model).offset(skip).limit(limit)
        return list(self._db.exec(stmt).all())

    def create(self, entity: T) -> T:
        """Persiste una nueva entidad y devuelve la instancia con ID asignado."""
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """Actualiza una entidad existente (ya modificada en memoria)."""
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def delete(self, entity_id: int) -> bool:
        """
        Elimina la entidad con el ID dado.

        Returns
        -------
        bool
            True si se eliminó, False si no existía.
        """
        entity = self.get(entity_id)
        if entity is None:
            return False
        self._db.delete(entity)
        self._db.commit()
        return True

    def flush_add(self, entity: T) -> T:
        """Agrega la entidad y hace flush (sin commit) para obtener el ID."""
        self._db.add(entity)
        self._db.flush()
        return entity
