import pytest
from sqlmodel import Session
from src.models.category import Category
from src.models.intake_type import IntakeType
from src.models.medication import Medication


@pytest.fixture()
def category(db: Session):
    cat = Category(name="Test Category", description="For prediction tests")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    yield cat
    db.delete(cat)
    db.commit()


@pytest.fixture()
def intake_type(db: Session):
    it = IntakeType(name="Test Intake", description="For prediction tests")
    db.add(it)
    db.commit()
    db.refresh(it)
    yield it
    db.delete(it)
    db.commit()


@pytest.fixture()
def medication(db: Session, category: Category, intake_type: IntakeType):
    med = Medication(
        name="TestMed",
        stock=50,
        min_stock=5,
        unit="units",
        status="Activo",
        price=1.0,
        category_id=category.id,
        intake_type_id=intake_type.id,
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    yield med
    db.delete(med)
    db.commit()


class TestListPredictions:
    def test_requires_authentication(self, client):
        response = client.get("/api/v1/predictions/")
        assert response.status_code == 401

    def test_authenticated_returns_list(self, client, user_token):
        response = client.get(
            "/api/v1/predictions/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_filter_by_medication_id(self, client, user_token, medication):
        response = client.get(
            f"/api/v1/predictions/?medication_id={medication.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200


class TestPredictShortageRisk:
    def test_requires_authentication(self, client, medication):
        response = client.post(f"/api/v1/predictions/{medication.id}/predict")
        assert response.status_code == 401

    def test_nonexistent_medication_returns_error(self, client, user_token):
        response = client.post(
            "/api/v1/predictions/99999/predict",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # Should return 404 or 422 — not 200 — for a nonexistent medication
        assert response.status_code in (404, 422, 500)

    def test_medication_with_no_history_returns_error(self, client, user_token, medication):
        response = client.post(
            f"/api/v1/predictions/{medication.id}/predict",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # No historical data → should return 422 or 500, not 200
        assert response.status_code in (422, 500)
