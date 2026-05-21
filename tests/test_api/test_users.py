import pytest
from sqlmodel import Session
from src.models.user import User
from src.models.base import Role, UserStatus


class TestLogin:
    def test_valid_credentials_returns_token(self, client, admin_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": admin_user.email, "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == admin_user.email
        assert data["user"]["role"] == Role.ADMIN.value

    def test_invalid_password_returns_401(self, client, admin_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": admin_user.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_unknown_email_returns_401(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "unknown@test.com", "password": "anypassword"},
        )
        assert response.status_code == 401

    def test_missing_fields_returns_422(self, client):
        response = client.post("/api/v1/auth/login", json={"username": "test@test.com"})
        assert response.status_code == 422

    def test_login_sets_cookie(self, client, admin_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": admin_user.email, "password": "admin123"},
        )
        assert response.status_code == 200
        assert "access_token" in response.cookies


class TestRegister:
    def test_new_user_registers_successfully(self, client, db):
        payload = {
            "name": "Nuevo Usuario",
            "email": "nuevo@test.com",
            "password": "nuevo123",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "nuevo@test.com"
        assert "access_token" in data
        # Cleanup
        user = db.query(User).filter(User.email == "nuevo@test.com").first()
        if user:
            db.delete(user)
            db.commit()

    def test_duplicate_email_returns_400(self, client, admin_user):
        payload = {
            "name": "Duplicado",
            "email": admin_user.email,
            "password": "duplicado123",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 400

    def test_short_password_returns_422(self, client):
        payload = {
            "name": "Test",
            "email": "shortpass@test.com",
            "password": "123",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    def test_missing_email_returns_422(self, client):
        payload = {"name": "Test", "password": "valid123"}
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


class TestLogout:
    def test_logout_clears_cookie(self, client, admin_token):
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Sesión cerrada exitosamente"

    def test_logout_without_auth_still_succeeds(self, client):
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200


class TestCurrentUser:
    def test_get_me_returns_user_data(self, client, admin_token, admin_user):
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == admin_user.email
        assert data["role"] == Role.ADMIN.value

    def test_get_me_without_auth_returns_401(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_cookie_auth_works_for_me(self, client, admin_user):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": admin_user.email, "password": "admin123"},
        )
        assert login_response.status_code == 200
        # Cookie is automatically sent by TestClient on subsequent requests
        me_response = client.get("/api/v1/users/me")
        assert me_response.status_code == 200
        assert me_response.json()["email"] == admin_user.email


class TestAdminUserManagement:
    def test_list_users_requires_admin(self, client, user_token):
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_admin_can_list_users(self, client, admin_token, admin_user):
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert any(u["email"] == admin_user.email for u in users)

    def test_get_user_by_id(self, client, admin_token, regular_user):
        response = client.get(
            f"/api/v1/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == regular_user.email

    def test_get_nonexistent_user_returns_404(self, client, admin_token):
        response = client.get(
            "/api/v1/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
