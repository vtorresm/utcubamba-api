"""
Capa de repositorios — implementación del patrón Repository.

Separa la lógica de acceso a datos del dominio de negocio.
Cada repositorio concreto hereda de BaseRepository[T] y encapsula
las operaciones CRUD y las consultas específicas del modelo.
"""

from .base import BaseRepository
from .medication_repository import MedicationRepository
from .forecast_repository import ForecastRepository
from .movement_repository import MovementRepository

__all__ = [
    "BaseRepository",
    "MedicationRepository",
    "ForecastRepository",
    "MovementRepository",
]
