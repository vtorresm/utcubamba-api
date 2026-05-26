import logging
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def _get_engine():
    from src.core.config import settings
    echo_sql = settings.ENVIRONMENT != "production"
    engine = create_engine(
        settings.DATABASE_URL,
        echo=echo_sql,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    return engine


engine = _get_engine()
SessionLocal = sessionmaker(bind=engine, class_=Session)


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
    SQLModel.metadata.create_all(engine)
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
