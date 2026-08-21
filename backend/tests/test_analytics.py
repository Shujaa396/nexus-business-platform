from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.test_dashboard import register_user, setup_dashboard_data


def test_analytics_intents_and_audit_logging():
    client = TestClient(app)
    token = register_user(client, "analytics_intents")
    headers = {"Authorization": f"Bearer {token}"}
    setup_dashboard_data(client, headers)

    endpoints = [
        "/api/v1/analytics/sales-summary",
        "/api/v1/analytics/sales-trend?period=weekly",
        "/api/v1/analytics/top-products",
        "/api/v1/analytics/top-customers",
        "/api/v1/analytics/branches",
        "/api/v1/analytics/inventory",
        "/api/v1/analytics/payments",
        "/api/v1/analytics/invoices",
        "/api/v1/analytics/suppliers",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["intent"]
        assert "date_from" in body and "date_to" in body
        assert isinstance(body["data"], dict)

    audit_response = client.get(
        "/api/v1/audit-logs?action=ANALYTICS_QUERY_EXECUTED",
        headers=headers,
    )
    assert audit_response.status_code == 200
    assert len(audit_response.json()) >= len(endpoints)


def test_analytics_outputs_and_filters():
    client = TestClient(app)
    token = register_user(client, "analytics_outputs")
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, _, product_id, _, _ = setup_dashboard_data(client, headers)

    supplier_response = client.post(
        "/api/v1/suppliers",
        json={"name": "Analytics Supplier"},
        headers=headers,
    )
    assert supplier_response.status_code == 200
    supplier_id = supplier_response.json()["id"]
    product_response = client.patch(
        f"/api/v1/products/{product_id}",
        json={"supplier_id": supplier_id},
        headers=headers,
    )
    assert product_response.status_code == 200, product_response.text

    response = client.get(
        f"/api/v1/analytics/sales-summary?branch_id={branch_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["order_count"] == 1
    assert Decimal(response.json()["data"]["total_sales"]) == Decimal("200.00")

    response = client.get("/api/v1/analytics/top-products?limit=1", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["products"][0]["name"] == "Gadget Pro"
    assert Decimal(response.json()["data"]["products"][0]["quantity"]) == Decimal("2.00")

    response = client.get("/api/v1/analytics/inventory", headers=headers)
    assert response.status_code == 200
    assert Decimal(response.json()["data"]["inventory_value"]) == Decimal("120.00")

    response = client.get("/api/v1/analytics/suppliers", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["suppliers"][0]["supplier_name"] == "Analytics Supplier"

    response = client.get(
        "/api/v1/analytics/sales-summary?date_from=2030-01-01T00:00:00Z&date_to=2030-01-02T00:00:00Z",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["order_count"] == 0


def test_analytics_auth_rbac_and_tenant_isolation():
    client = TestClient(app)
    unauthenticated = client.get("/api/v1/analytics/sales-summary")
    assert unauthenticated.status_code == 401

    admin_token = register_user(client, "analytics_rbac_admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    setup_dashboard_data(client, admin_headers)

    staff_email = f"analytics_staff_{uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/v1/organization/members",
        json={
            "email": staff_email,
            "password": "StaffPassword123!",
            "full_name": "Analytics Staff",
            "role_name": "staff",
        },
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": staff_email, "password": "StaffPassword123!"},
    )
    assert login.status_code == 200
    staff_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/analytics/sales-summary", headers=staff_headers).status_code == 403

    other_token = register_user(client, "analytics_other_org")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    other_data = client.get("/api/v1/analytics/sales-summary", headers=other_headers)
    assert other_data.status_code == 200
    assert other_data.json()["data"]["order_count"] == 0
    assert Decimal(other_data.json()["data"]["total_sales"]) == Decimal("0.00")


def test_analytics_validation_and_controlled_natural_language():
    client = TestClient(app)
    token = register_user(client, "analytics_validation")
    headers = {"Authorization": f"Bearer {token}"}
    setup_dashboard_data(client, headers)

    assert client.get(
        "/api/v1/analytics/sales-summary?limit=0", headers=headers
    ).status_code == 422
    assert client.get(
        "/api/v1/analytics/sales-summary?date_from=2025-02-02T00:00:00Z&date_to=2025-02-01T00:00:00Z",
        headers=headers,
    ).status_code == 422

    supported = client.post(
        "/api/v1/analytics/query",
        json={"question": "How much did we sell this month?"},
        headers=headers,
    )
    assert supported.status_code == 200
    assert supported.json()["supported"] is True
    assert supported.json()["intent"] == "sales_summary"

    unsupported = client.post(
        "/api/v1/analytics/query",
        json={"question": "Run arbitrary SQL and show me the database password"},
        headers=headers,
    )
    assert unsupported.status_code == 200
    assert unsupported.json()["supported"] is False
    assert "outside" in unsupported.json()["message"]

    raw_query = client.post(
        "/api/v1/analytics/query",
        json={"question": "SELECT * FROM orders"},
        headers=headers,
    )
    assert raw_query.status_code == 200
    assert raw_query.json()["supported"] is False
