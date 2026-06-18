"""
Patrón Singleton — DatabaseSingleton.

Garantiza que solo exista una instancia del motor de base de datos
en toda la aplicación, independientemente de cuántas veces se
instancie DatabaseSingleton.  La unicidad se implementa sobrescribiendo
__new__, el mecanismo de Python para controlar la creación de objetos.

Uso
---
    engine = DatabaseSingleton().engine
    session_factory = DatabaseSingleton().session_factory
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)


class DatabaseSingleton:
    """
    Singleton que gestiona el motor SQLAlchemy compartido.

    La primera llamada a DatabaseSingleton() crea el motor y la fábrica
    de sesiones; las llamadas subsecuentes devuelven la misma instancia,
    lo que evita la creación de múltiples connection pools.

    Attributes
    ----------
    engine : sqlalchemy.engine.Engine
        Motor SQLAlchemy/SQLModel listo para usar.
    session_factory : sessionmaker
        Fábrica de sesiones configurada con el engine compartido.
    """

    _instance: Optional["DatabaseSingleton"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "DatabaseSingleton":
        """Controla la creación: devuelve la instancia existente si ya existe."""
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking: re-verificar dentro del lock
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        # Evitar re-inicialización en llamadas posteriores
        if self._initialized:
            return
        self._initialized = True
        self._setup_engine()

    def _setup_engine(self) -> None:
        """Crea el engine y la session factory usando la configuración global."""
        from src.core.config import settings

        echo_sql = settings.ENVIRONMENT != "production"
        self.engine = create_engine(
            settings.DATABASE_URL,
            echo=echo_sql,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        self.session_factory = sessionmaker(bind=self.engine, class_=Session)
        logger.info("DatabaseSingleton: engine creado (pool_recycle=300s)")

    @classmethod
    def reset(cls) -> None:
        """
        Reinicia la instancia singleton (útil en tests de integración
        para forzar la creación de un engine con nueva URL).
        """
        with cls._lock:
            cls._instance = None
