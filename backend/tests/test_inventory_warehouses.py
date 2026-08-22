from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.test_dashboard import register_user


def setup_warehouses(client: TestClient, headers: dict[str, str]):
    branch = client.post("/api/v1/branches", json={"code": f"WH-{uuid4().hex[:6]}", "name": "Warehouse Branch"}, headers=headers)
    assert branch.status_code == 200, branch.text
    product = client.post("/api/v1/products", json={"sku": f"WH-SKU-{uuid4().hex[:6]}", "name": "Warehouse Product", "unit": "unit", "cost_price": "4.00", "selling_price": "8.00", "tax_rate": "0"}, headers=headers)
    assert product.status_code == 200, product.text
    warehouses = []
    for code in ("MAIN", "SECOND"):
        response = client.post("/api/v1/warehouses", json={"name": f"{code} Warehouse", "code": f"{code}-{uuid4().hex[:4]}", "branch_id": branch.json()["id"]}, headers=headers)
        assert response.status_code == 201, response.text
        warehouses.append(response.json())
    return branch.json(), product.json(), warehouses


def test_warehouse_inventory_transfers_reservations_and_valuation():
    client = TestClient(app)
    token = register_user(client, "warehouse_ops")
    headers = {"Authorization": f"Bearer {token}"}
    branch, product, warehouses = setup_warehouses(client, headers)
    source, destination = warehouses

    created = client.post("/api/v1/inventory/adjustments", json={"warehouse_id": source["id"], "product_id": product["id"], "quantity": "100", "reason": "Initial count"}, headers=headers)
    assert created.status_code == 200, created.text
    assert Decimal(created.json()["quantity"]) == Decimal("100")

    reservation = client.post("/api/v1/inventory/reservations", json={"warehouse_id": source["id"], "product_id": product["id"], "quantity": "20", "reference_type": "TEST"}, headers=headers)
    assert reservation.status_code == 201, reservation.text
    inventory = client.get(f"/api/v1/inventory/by-warehouse?warehouse_id={source['id']}", headers=headers)
    assert inventory.status_code == 200
    assert Decimal(inventory.json()[0]["available_quantity"]) == Decimal("80")

    over = client.post("/api/v1/inventory/reservations", json={"warehouse_id": source["id"], "product_id": product["id"], "quantity": "81"}, headers=headers)
    assert over.status_code == 400
    assert client.post(f"/api/v1/inventory/reservations/{reservation.json()['id']}/release", headers=headers).status_code == 200

    transfer = client.post("/api/v1/inventory/transfers", json={"source_warehouse_id": source["id"], "destination_warehouse_id": destination["id"], "items": [{"product_id": product["id"], "quantity": "30"}]}, headers=headers)
    assert transfer.status_code == 201, transfer.text
    transfer_id = transfer.json()["id"]
    assert client.post(f"/api/v1/inventory/transfers/{transfer_id}/approve", headers=headers).status_code == 200
    assert client.post(f"/api/v1/inventory/transfers/{transfer_id}/dispatch", headers=headers).status_code == 200
    received = client.post(f"/api/v1/inventory/transfers/{transfer_id}/receive", headers=headers)
    assert received.status_code == 200, received.text
    assert received.json()["status"] == "COMPLETED"
    duplicate = client.post(f"/api/v1/inventory/transfers/{transfer_id}/receive", headers=headers)
    assert duplicate.status_code == 400

    source_inventory = client.get(f"/api/v1/inventory/by-warehouse?warehouse_id={source['id']}", headers=headers).json()[0]
    destination_inventory = client.get(f"/api/v1/inventory/by-warehouse?warehouse_id={destination['id']}", headers=headers).json()[0]
    assert Decimal(source_inventory["quantity"]) == Decimal("70")
    assert Decimal(destination_inventory["quantity"]) == Decimal("30")

    valuation = client.get("/api/v1/inventory/valuation", headers=headers)
    assert valuation.status_code == 200
    assert Decimal(valuation.json()["total_inventory_value"]) == Decimal("400")
    movements = client.get(f"/api/v1/inventory/movements?warehouse_id={source['id']}", headers=headers)
    assert movements.status_code == 200
    assert {row["transaction_type"] for row in movements.json()} >= {"ADJUSTMENT", "TRANSFER_OUT"}


def test_warehouse_rbac_tenant_isolation_and_deactivation():
    client = TestClient(app)
    admin_token = register_user(client, "warehouse_admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    branch, product, warehouses = setup_warehouses(client, admin_headers)
    warehouse = warehouses[0]

    other_token = register_user(client, "warehouse_other")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/warehouses/{warehouse['id']}", headers=other_headers).status_code == 404
    assert client.get(f"/api/v1/inventory/by-warehouse?warehouse_id={warehouse['id']}", headers=other_headers).json() == []

    staff_email = f"warehouse_staff_{uuid4().hex[:8]}@example.com"
    member = client.post("/api/v1/organization/members", json={"email": staff_email, "password": "StaffPassword123!", "full_name": "Warehouse Staff", "role_name": "staff"}, headers=admin_headers)
    assert member.status_code == 200, member.text
    login = client.post("/api/v1/auth/login", json={"email": staff_email, "password": "StaffPassword123!"})
    staff_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/warehouses", headers=staff_headers).status_code == 200
    assert client.post("/api/v1/warehouses", json={"name": "Nope", "code": "NOPE", "branch_id": branch["id"]}, headers=staff_headers).status_code == 403

    assert client.delete(f"/api/v1/warehouses/{warehouse['id']}", headers=admin_headers).status_code == 200
    assert client.get(f"/api/v1/warehouses/{warehouse['id']}", headers=admin_headers).json()["is_active"] is False


def test_purchase_order_receives_into_selected_warehouse():
    client = TestClient(app)
    token = register_user(client, "warehouse_purchase")
    headers = {"Authorization": f"Bearer {token}"}
    branch, product, warehouses = setup_warehouses(client, headers)
    supplier = client.post("/api/v1/suppliers", json={"name": "Warehouse Supplier"}, headers=headers)
    assert supplier.status_code == 200
    order = client.post("/api/v1/purchase-orders", json={"supplier_id": supplier.json()["id"], "branch_id": branch["id"], "warehouse_id": warehouses[0]["id"], "items": [{"product_id": product["id"], "quantity": "12", "unit_cost": "4.00"}]}, headers=headers)
    assert order.status_code == 201, order.text
    order_id = order.json()["id"]
    assert client.post(f"/api/v1/purchase-orders/{order_id}/submit", headers=headers).status_code == 200
    assert client.post(f"/api/v1/purchase-orders/{order_id}/approve", headers=headers).status_code == 200
    received = client.post(f"/api/v1/purchase-orders/{order_id}/receive", json={"receipt_reference": "WH-GRN-1", "items": [{"item_id": order.json()["items"][0]["id"], "quantity": "12"}]}, headers=headers)
    assert received.status_code == 200, received.text
    replay = client.post(f"/api/v1/purchase-orders/{order_id}/receive", json={"receipt_reference": "WH-GRN-1", "items": [{"item_id": order.json()["items"][0]["id"], "quantity": "12"}]}, headers=headers)
    assert replay.status_code == 200, replay.text
    assert replay.json()["items"][0]["received_quantity"] == "12.0000"
    inventory = client.get(f"/api/v1/inventory/by-warehouse?warehouse_id={warehouses[0]['id']}", headers=headers)
    assert inventory.status_code == 200
    assert Decimal(inventory.json()[0]["quantity"]) == Decimal("12")
