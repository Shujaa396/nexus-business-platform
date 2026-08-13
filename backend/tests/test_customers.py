from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def register_and_token(client: TestClient):
    email = _unique_email("cust")
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Cust User",
        "organization_name": "Cust Org",
        "organization_slug": f"cust-org-{uuid4().hex[:8]}",
    }
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"]


def test_customers_crud_and_isolation():
    client = TestClient(app)
    token = register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # create customer
    resp = client.post("/api/v1/customers", json={"name": "Alice"}, headers=headers)
    assert resp.status_code == 200, resp.text
    cust = resp.json()
    cust_id = cust["id"]

    # list
    resp = client.get("/api/v1/customers", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert any(it["id"] == cust_id for it in items)

    # get detail
    resp = client.get(f"/api/v1/customers/{cust_id}", headers=headers)
    assert resp.status_code == 200

    # patch
    resp = client.patch(f"/api/v1/customers/{cust_id}", json={"name": "Alice B"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice B"

    # soft delete
    resp = client.delete(f"/api/v1/customers/{cust_id}", headers=headers)
    assert resp.status_code == 200

    # other org cannot see
    token2 = register_and_token(client)
    headers2 = {"Authorization": f"Bearer {token2}"}
    resp = client.get(f"/api/v1/customers/{cust_id}", headers=headers2)
    assert resp.status_code == 404
