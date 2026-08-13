from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def test_register_login_and_me_flow() -> None:
    client = TestClient(app)
    email = _unique_email("register")
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Test User",
        "organization_name": "Demo Org",
        "organization_slug": f"demo-org-{uuid4().hex[:8]}",
    }

    register_response = client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200, register_response.text
    register_data = register_response.json()
    assert register_data["user"]["email"] == email
    assert "access_token" in register_data
    assert "refresh_token" in register_data

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123!"},
    )
    assert login_response.status_code == 200, login_response.text
    login_data = login_response.json()
    assert login_data["user"]["email"] == email
    assert login_data["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["email"] == email


def test_refresh_token_returns_new_access_token() -> None:
    client = TestClient(app)
    email = _unique_email("refresh")
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Refresh User",
        "organization_name": "Refresh Org",
        "organization_slug": f"refresh-org-{uuid4().hex[:8]}",
    }

    register_response = client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200, register_response.text
    refresh_token = register_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200, refresh_response.text
    data = refresh_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_missing_auth_token_is_rejected() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
