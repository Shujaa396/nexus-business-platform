from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email(prefix: str = "dash_user") -> str:
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def register_user(client: TestClient, prefix: str = "dash"):
    email = _unique_email(prefix)
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Dashboard User",
        "organization_name": f"Org {prefix}",
        "organization_slug": f"org-{prefix}-{uuid4().hex[:8]}",
    }
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def setup_dashboard_data(client: TestClient, headers: dict):
    # 1. Create Branch
    r = client.post("/api/v1/branches", json={"code": f"B-{uuid4().hex[:4]}", "name": "Main Branch"}, headers=headers)
    assert r.status_code == 200, r.text
    branch_id = r.json()["id"]

    # 2. Create Customer
    r = client.post("/api/v1/customers", json={"name": "Alice Corp", "email": "alice@example.com"}, headers=headers)
    assert r.status_code == 200, r.text
    customer_id = r.json()["id"]

    # 3. Create Product
    prod_payload = {
        "sku": f"SKU-{uuid4().hex[:6]}",
        "name": "Gadget Pro",
        "description": "Pro gadget",
        "unit": "pcs",
        "cost_price": "40.00",
        "selling_price": "100.00",
        "tax_rate": "0.10",
        "category_id": None,
    }
    r = client.post("/api/v1/products", json=prod_payload, headers=headers)
    assert r.status_code == 200, r.text
    product_id = r.json()["id"]

    # 4. Stock in
    r = client.post(
        "/api/v1/inventory/stock-in",
        json={"branch_id": branch_id, "product_id": product_id, "quantity": "5"},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    # 5. Create and confirm Order
    order_payload = {
        "branch_id": branch_id,
        "customer_id": customer_id,
        "items": [
            {
                "product_id": product_id,
                "quantity": "2",
                "unit_price": "100.00",
                "discount": "0.00",
                "tax": "0.00",
            }
        ],
    }
    r = client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert r.status_code == 200, r.text
    order_id = r.json()["id"]

    r_confirm = client.post(f"/api/v1/orders/{order_id}/confirm", headers=headers)
    assert r_confirm.status_code == 200, r_confirm.text

    # 6. Generate Invoice
    r_inv = client.post("/api/v1/invoices", json={"order_id": order_id}, headers=headers)
    assert r_inv.status_code == 201, r_inv.text
    inv_id = r_inv.json()["id"]

    # Issue & Record Payment
    client.post(f"/api/v1/invoices/{inv_id}/issue", headers=headers)
    client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": "200.00", "payment_method": "CASH"},
        headers=headers,
    )

    return branch_id, customer_id, product_id, order_id, inv_id


def test_dashboard_summary():
    client = TestClient(app)
    token = register_user(client, "summary")
    headers = {"Authorization": f"Bearer {token}"}

    setup_dashboard_data(client, headers)

    r = client.get("/api/v1/dashboard/summary", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["total_products"] >= 1
    assert data["total_customers"] >= 1
    assert data["total_orders"] >= 1
    assert data["total_invoices"] >= 1
    assert Decimal(str(data["total_revenue"])) == Decimal("200.00")
    assert Decimal(str(data["total_payments"])) == Decimal("200.00")
    assert Decimal(str(data["pending_payments"])) == Decimal("0.00")
    assert data["today_orders"] >= 1
    assert Decimal(str(data["today_sales"])) == Decimal("200.00")


def test_sales_analytics():
    client = TestClient(app)
    token = register_user(client, "sales_an")
    headers = {"Authorization": f"Bearer {token}"}

    setup_dashboard_data(client, headers)

    r = client.get("/api/v1/dashboard/sales?preset=today&period_type=daily", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["preset"] == "today"
    assert data["total_orders"] >= 1
    assert Decimal(str(data["total_revenue"])) == Decimal("200.00")
    assert Decimal(str(data["total_payments"])) == Decimal("200.00")
    assert len(data["breakdown"]) >= 1

    # Test shortcuts
    r_daily = client.get("/api/v1/dashboard/sales/daily", headers=headers)
    assert r_daily.status_code == 200
    r_weekly = client.get("/api/v1/dashboard/sales/weekly", headers=headers)
    assert r_weekly.status_code == 200
    r_monthly = client.get("/api/v1/dashboard/sales/monthly", headers=headers)
    assert r_monthly.status_code == 200


def test_product_analytics():
    client = TestClient(app)
    token = register_user(client, "prod_an")
    headers = {"Authorization": f"Bearer {token}"}

    setup_dashboard_data(client, headers)

    r = client.get("/api/v1/dashboard/products", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()

    assert len(data["top_selling_products"]) >= 1
    assert data["top_selling_products"][0]["name"] == "Gadget Pro"
    assert Decimal(str(data["top_selling_products"][0]["units_sold"])) == Decimal("2")

    assert len(data["highest_revenue_products"]) >= 1
    assert Decimal(str(data["total_inventory_value"])) > Decimal("0")


def test_customer_analytics():
    client = TestClient(app)
    token = register_user(client, "cust_an")
    headers = {"Authorization": f"Bearer {token}"}

    setup_dashboard_data(client, headers)

    r = client.get("/api/v1/dashboard/customers?preset=today", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["total_customers"] >= 1
    assert data["new_customers_in_period"] >= 1
    assert len(data["top_customers"]) >= 1
    assert data["top_customers"][0]["name"] == "Alice Corp"
    assert Decimal(str(data["top_customers"][0]["total_spent"])) == Decimal("200.00")


def test_branch_analytics():
    client = TestClient(app)
    token = register_user(client, "br_an")
    headers = {"Authorization": f"Bearer {token}"}

    setup_dashboard_data(client, headers)

    r = client.get("/api/v1/dashboard/branches", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()

    assert len(data["branches"]) >= 1
    b = data["branches"][0]
    assert b["name"] == "Main Branch"
    assert b["order_count"] >= 1
    assert Decimal(str(b["revenue"])) == Decimal("200.00")


def test_dashboard_tenant_isolation():
    client = TestClient(app)
    token1 = register_user(client, "iso1")
    headers1 = {"Authorization": f"Bearer {token1}"}

    token2 = register_user(client, "iso2")
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Org 1 populates data
    setup_dashboard_data(client, headers1)

    # Org 2 dashboard should show zero metrics
    r2 = client.get("/api/v1/dashboard/summary", headers=headers2)
    assert r2.status_code == 200, r2.text
    d2 = r2.json()

    assert d2["total_products"] == 0
    assert d2["total_customers"] == 0
    assert d2["total_orders"] == 0
    assert d2["total_invoices"] == 0
    assert Decimal(str(d2["total_revenue"])) == Decimal("0.00")
    assert Decimal(str(d2["total_payments"])) == Decimal("0.00")
