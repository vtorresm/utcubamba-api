import pytest
from sqlmodel import Session
from src.models.category import Category
from src.models.intake_type import IntakeType
from src.models.medication import Medication


@pytest.fixture()
def category(db: Session):
    cat = Category(name="Analgésicos", description="Medicamentos para el dolor")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    yield cat
    db.delete(cat)
    db.commit()


@pytest.fixture()
def intake_type(db: Session):
    it = IntakeType(name="Oral", description="Vía oral")
    db.add(it)
    db.commit()
    db.refresh(it)
    yield it
    db.delete(it)
    db.commit()


@pytest.fixture()
def medication(db: Session, category: Category, intake_type: IntakeType):
    med = Medication(
        name="Paracetamol",
        stock=100,
        min_stock=10,
        unit="comprimidos",
        status="Activo",
        price=5.0,
        category_id=category.id,
        intake_type_id=intake_type.id,
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    yield med
    db.delete(med)
    db.commit()


class TestListMedications:
    def test_returns_paginated_list(self, client, medication, admin_token):
        response = client.get(
            "/api/v1/medications/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_pagination_skip_limit(self, client, medication, admin_token):
        response = client.get(
            "/api/v1/medications/?skip=0&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) <= 5

    def test_filter_by_name(self, client, medication, admin_token):
        response = client.get(
            "/api/v1/medications/?name=Paracetamol",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        items = response.json()["items"]
        assert any("Paracetamol" in item["name"] for item in items)


class TestGetMedicationById:
    def test_not_found_returns_404(self, client, admin_token):
        response = client.get(
            "/api/v1/medications/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_existing_medication_returns_data(self, client, medication, admin_token):
        response = client.get(
            f"/api/v1/medications/{medication.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Paracetamol"
        assert data["data"]["stock"] == 100


class TestCreateMedication:
    def test_non_admin_gets_403(self, client, user_token, category, intake_type):
        payload = {
            "name": "Amoxicilina",
            "stock": 50,
            "min_stock": 5,
            "unit": "cápsulas",
            "status": "Activo",
            "price": 10.0,
            "category_id": category.id,
            "intake_type_id": intake_type.id,
        }
        response = client.post(
            "/api/v1/medications/",
            json=payload,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_unauthenticated_gets_401(self, client, category, intake_type):
        payload = {
            "name": "Amoxicilina",
            "stock": 50,
            "min_stock": 5,
            "unit": "cápsulas",
            "status": "Activo",
            "price": 10.0,
        }
        response = client.post("/api/v1/medications/", json=payload)
        assert response.status_code == 401

    def test_admin_creates_medication(self, client, admin_token, category, intake_type, db):
        payload = {
            "name": "Ibuprofeno",
            "stock": 200,
            "min_stock": 20,
            "unit": "comprimidos",
            "status": "Activo",
            "price": 8.0,
            "category_id": category.id,
            "intake_type_id": intake_type.id,
        }
        response = client.post(
            "/api/v1/medications/",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        created = response.json()
        assert created["name"] == "Ibuprofeno"
        assert created["stock"] == 200
        # Cleanup
        med = db.query(Medication).filter(Medication.name == "Ibuprofeno").first()
        if med:
            db.delete(med)
            db.commit()


class TestUpdateMedication:
    def test_non_admin_gets_403(self, client, medication, user_token):
        response = client.put(
            f"/api/v1/medications/{medication.id}",
            json={"stock": 999},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_admin_updates_medication(self, client, medication, admin_token, db):
        response = client.put(
            f"/api/v1/medications/{medication.id}",
            json={"stock": 999},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["stock"] == 999


class TestDeleteMedication:
    def test_non_admin_gets_403(self, client, medication, user_token):
        response = client.delete(
            f"/api/v1/medications/{medication.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_admin_deletes_medication(self, client, medication, admin_token, db):
        response = client.delete(
            f"/api/v1/medications/{medication.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204
        assert db.get(Medication, medication.id) is None
