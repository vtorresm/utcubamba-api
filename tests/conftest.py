import os

# Set test env vars before any app imports so config/database use SQLite
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-purposes-only-not-for-production")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("MAILTRAP_HOST", "")
os.environ.setdefault("MAILTRAP_PORT", "587")
os.environ.setdefault("MAILTRAP_USERNAME", "")
os.environ.setdefault("MAILTRAP_PASSWORD", "")
os.environ.setdefault("MAIL_FROM", "test@test.com")
os.environ.setdefault("MAIL_FROM_NAME", "Test")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

# Import all models before creating tables (registers them with SQLModel metadata)
from src.models.base import Role, UserStatus
from src.models.user import User
from src.models.category import Category
from src.models.condition import Condition
from src.models.intake_type import IntakeType
from src.models.medication import Medication
from src.models.movement import Movement
from src.models.prediction import Prediction, PredictionMetrics
from src.models.medication_condition import MedicationConditionLink
from src.models.password_reset_token import PasswordResetToken
from src.models.notification import Notification, NotificationType, NotificationLevel
from src.models.order import Order, OrderStatus
from src.models.report import Report, ReportType, ReportFormat, ReportStatus

# Create a shared in-memory SQLite engine for tests (StaticPool = one DB shared by all connections)
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(TEST_ENGINE)

# Import app after env vars and models are ready
from src.main import app
from src.core.database import get_db


@pytest.fixture()
def db():
    with Session(TEST_ENGINE) as session:
        yield session


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db):
    user = User(
        nombre="Admin Test",
        email="admin_fixture@test.com",
        hashed_password=User.hash_password("admin123"),
        cargo="Administrador",
        departamento="IT",
        role=Role.ADMIN,
        estado=UserStatus.ACTIVO,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture()
def regular_user(db):
    user = User(
        nombre="User Test",
        email="user_fixture@test.com",
        hashed_password=User.hash_password("user123"),
        cargo="Farmacéutico",
        departamento="Farmacia",
        role=Role.USER,
        estado=UserStatus.ACTIVO,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture()
def admin_token(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.email, "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def user_token(client, regular_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": regular_user.email, "password": "user123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
