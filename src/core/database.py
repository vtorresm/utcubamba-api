import logging
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.orm import sessionmaker

# Patron Singleton: el engine se gestiona a traves de DatabaseSingleton
# para garantizar una unica instancia del connection pool en toda la app.
from src.core.singleton import DatabaseSingleton

logger = logging.getLogger(__name__)

# Obtener el engine desde el Singleton (crea el pool si es la primera vez)
_db_singleton = DatabaseSingleton()
engine = _db_singleton.engine
SessionLocal = _db_singleton.session_factory


def _import_models():
    from src.models.user import User, UserCreate, UserUpdate, UserInDB
    from src.models.category import Category, CategoryCreate, CategoryUpdate, CategoryInDB
    from src.models.condition import Condition, ConditionCreate, ConditionUpdate, ConditionInDB
    from src.models.intake_type import IntakeType, IntakeTypeCreate, IntakeTypeUpdate, IntakeTypeInDB
    from src.models.medication import Medication, MedicationCreate, MedicationUpdate, MedicationInDB
    from src.models.movement import Movement, MovementCreate, MovementUpdate, MovementInDB
    from src.models.prediction import Prediction, PredictionCreate, PredictionUpdate, PredictionInDB
    from src.models.medication_condition import MedicationConditionLink
    from src.models.notification import Notification, NotificationCreate, NotificationUpdate, NotificationInDB
    from src.models.order import Order, OrderCreate, OrderUpdate, OrderInDB
    from src.models.report import Report, ReportCreate, ReportUpdate, ReportInDB
    logger.debug("All models imported successfully")


def create_db_and_tables():
    _import_models()
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(DatabaseSingleton().engine)
    logger.info("Database tables created successfully")


# Alias kept for Alembic compatibility
SQLALCHEMY_DATABASE_URL: str
try:
    from src.core.config import settings as _s
    SQLALCHEMY_DATABASE_URL = _s.DATABASE_URL
except Exception:
    SQLALCHEMY_DATABASE_URL = ""


def get_db() -> Generator[Session, None, None]:
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


_import_models()
