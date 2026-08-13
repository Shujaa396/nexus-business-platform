from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def register_and_token(client: TestClient):
    email = _unique_email("ord")
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Order User",
        "organization_name": "Order Org",
        "organization_slug": f"order-org-{uuid4().hex[:8]}",
    }
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"]


def setup_branch_and_product(client: TestClient, headers):
    # create branch
    r = client.post("/api/v1/branches", json={"code": "BR1", "name": "Default"}, headers=headers)
    assert r.status_code == 200, r.text
    branch_id = r.json()["id"]

    # create product
    prod_payload = {
        "sku": f"SKU-{uuid4().hex[:6]}",
        "name": "Widget",
        "description": "Test",
        "unit": "pcs",
        "cost_price": "10.00",
        "selling_price": "15.00",
        "tax_rate": "0",
        "category_id": None,
    }
    r = client.post("/api/v1/products", json=prod_payload, headers=headers)
    assert r.status_code == 200, r.text
    product = r.json()
    product_id = product["id"]

    # stock in
    r = client.post("/api/v1/inventory/stock-in", json={"branch_id": branch_id, "product_id": product_id, "quantity": "100"}, headers=headers)
    assert r.status_code == 200, r.text
    return branch_id, product_id


def test_order_confirm_and_inventory_flow():
    client = TestClient(app)
    token = register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    branch_id, product_id = setup_branch_and_product(client, headers)

    # create order
    order_payload = {"branch_id": branch_id, "items": [{"product_id": product_id, "quantity": "2"}]}
    r = client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert r.status_code == 200, r.text
    order = r.json()
    order_id = order["id"]

    # confirm order
    r = client.post(f"/api/v1/orders/{order_id}/confirm", headers=headers)
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["status"] == "CONFIRMED"

    # check inventory decreased via listing
    r = client.get("/api/v1/inventory", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert any(it["product_id"] == product_id and Decimal(it["quantity"]) == Decimal("98") for it in items)

    # cancel order restores inventory
    r = client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["status"] == "CANCELLED"

    r = client.get("/api/v1/inventory", headers=headers)
    items = r.json()
    assert any(it["product_id"] == product_id and Decimal(it["quantity"]) == Decimal("100") for it in items)


def test_insufficient_stock_prevents_confirm():
    client = TestClient(app)
    token = register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, product_id = setup_branch_and_product(client, headers)

    # create order with large qty
    order_payload = {"branch_id": branch_id, "items": [{"product_id": product_id, "quantity": "1000"}]}
    r = client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert r.status_code == 200, r.text
    order = r.json()
    order_id = order["id"]

    r = client.post(f"/api/v1/orders/{order_id}/confirm", headers=headers)
    assert r.status_code == 400
