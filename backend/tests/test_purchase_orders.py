from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.test_dashboard import register_user


def setup_procurement_data(client: TestClient, headers: dict[str, str]):
    branch = client.post(
        "/api/v1/branches",
        json={"code": f"P-{uuid4().hex[:6]}", "name": "Procurement Branch"},
        headers=headers,
    )
    assert branch.status_code == 200, branch.text
    supplier = client.post(
        "/api/v1/suppliers",
        json={"name": "Procurement Supplier"},
        headers=headers,
    )
    assert supplier.status_code == 200, supplier.text
    product = client.post(
        "/api/v1/products",
        json={
            "sku": f"PO-SKU-{uuid4().hex[:6]}",
            "name": "Procurement Product",
            "unit": "box",
            "cost_price": "12.00",
            "selling_price": "20.00",
            "tax_rate": "0.00",
        },
        headers=headers,
    )
    assert product.status_code == 200, product.text
    return branch.json(), supplier.json(), product.json()


def create_po(client: TestClient, headers: dict[str, str], branch: dict, supplier: dict, product: dict, quantity: str = "10"):
    response = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": supplier["id"],
            "branch_id": branch["id"],
            "tax": "5.00",
            "discount": "2.00",
            "notes": "Quarterly replenishment",
            "items": [{"product_id": product["id"], "quantity": quantity, "unit_cost": "10.00"}],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_purchase_order_lifecycle_receiving_and_inventory():
    client = TestClient(app)
    token = register_user(client, "purchase_lifecycle")
    headers = {"Authorization": f"Bearer {token}"}
    branch, supplier, product = setup_procurement_data(client, headers)

    order = create_po(client, headers, branch, supplier, product)
    assert order["status"] == "DRAFT"
    assert Decimal(order["subtotal"]) == Decimal("100.00")
    assert Decimal(order["total"]) == Decimal("103.00")
    order_id = order["id"]
    item_id = order["items"][0]["id"]

    invalid_receive = client.post(
        f"/api/v1/purchase-orders/{order_id}/receive",
        json={"receipt_reference": "PRE-APPROVAL", "items": [{"item_id": item_id, "quantity": "2"}]},
        headers=headers,
    )
    assert invalid_receive.status_code == 400

    assert client.post(f"/api/v1/purchase-orders/{order_id}/submit", headers=headers).status_code == 200
    approved = client.post(f"/api/v1/purchase-orders/{order_id}/approve", headers=headers)
    assert approved.status_code == 200, approved.text
    assert approved.json()["purchase_order"]["status"] == "APPROVED"

    partial = client.post(
        f"/api/v1/purchase-orders/{order_id}/receive",
        json={"receipt_reference": "GRN-001", "items": [{"item_id": item_id, "quantity": "4"}]},
        headers=headers,
    )
    assert partial.status_code == 200, partial.text
    assert partial.json()["status"] == "PARTIALLY_RECEIVED"
    assert Decimal(partial.json()["items"][0]["received_quantity"]) == Decimal("4.00")

    duplicate = client.post(
        f"/api/v1/purchase-orders/{order_id}/receive",
        json={"receipt_reference": "GRN-001", "items": [{"item_id": item_id, "quantity": "4"}]},
        headers=headers,
    )
    assert duplicate.status_code == 400

    excessive = client.post(
        f"/api/v1/purchase-orders/{order_id}/receive",
        json={"receipt_reference": "GRN-OVER", "items": [{"item_id": item_id, "quantity": "7"}]},
        headers=headers,
    )
    assert excessive.status_code == 400

    duplicated_lines = client.post(
        f"/api/v1/purchase-orders/{order_id}/receive",
        json={"receipt_reference": "GRN-DUPLICATE-LINES", "items": [
            {"item_id": item_id, "quantity": "6"},
            {"item_id": item_id, "quantity": "5"},
        ]},
        headers=headers,
    )
    assert duplicated_lines.status_code == 400

    complete = client.post(
        f"/api/v1/purchase-orders/{order_id}/receive",
        json={"receipt_reference": "GRN-002", "items": [{"item_id": item_id, "quantity": "6"}]},
        headers=headers,
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "RECEIVED"

    inventory = client.get("/api/v1/inventory", headers=headers)
    assert inventory.status_code == 200
    inventory_row = next(row for row in inventory.json() if row["product_id"] == product["id"])
    assert Decimal(inventory_row["quantity"]) == Decimal("10.00")

    invalid_transition = client.post(f"/api/v1/purchase-orders/{order_id}/submit", headers=headers)
    assert invalid_transition.status_code == 400

    audit = client.get(
        "/api/v1/audit-logs?entity_type=PURCHASE_ORDER",
        headers=headers,
    )
    assert audit.status_code == 200
    actions = {entry["action"] for entry in audit.json()}
    assert {"PURCHASE_ORDER_CREATED", "PURCHASE_ORDER_SUBMITTED", "PURCHASE_ORDER_APPROVED", "PURCHASE_ORDER_STOCK_RECEIVED"} <= actions


def test_purchase_order_update_cancel_search_pagination_and_auth():
    client = TestClient(app)
    token = register_user(client, "purchase_controls")
    headers = {"Authorization": f"Bearer {token}"}
    branch, supplier, product = setup_procurement_data(client, headers)
    order = create_po(client, headers, branch, supplier, product, "3")

    updated = client.patch(
        f"/api/v1/purchase-orders/{order['id']}",
        json={"notes": "Updated draft", "items": [{"product_id": product["id"], "quantity": "5", "unit_cost": "11.00"}]},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert Decimal(updated.json()["total"]) == Decimal("58.00")

    assert client.post(f"/api/v1/purchase-orders/{order['id']}/submit", headers=headers).status_code == 200
    cancelled = client.post(f"/api/v1/purchase-orders/{order['id']}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["purchase_order"]["status"] == "CANCELLED"

    listing = client.get(
        f"/api/v1/purchase-orders?purchase_order_number={order['purchase_order_number']}&page=1&page_size=1",
        headers=headers,
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    assert client.get("/api/v1/purchase-orders").status_code == 401
    assert client.get("/api/v1/purchase-orders?limit=1", headers=headers).status_code == 200


def test_purchase_order_rbac_and_tenant_validation():
    client = TestClient(app)
    admin_token = register_user(client, "purchase_rbac_admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    branch, supplier, product = setup_procurement_data(client, admin_headers)
    order = create_po(client, admin_headers, branch, supplier, product)

    staff_email = f"purchase_staff_{uuid4().hex[:8]}@example.com"
    member = client.post(
        "/api/v1/organization/members",
        json={"email": staff_email, "password": "StaffPassword123!", "full_name": "Staff", "role_name": "staff"},
        headers=admin_headers,
    )
    assert member.status_code == 200, member.text
    login = client.post("/api/v1/auth/login", json={"email": staff_email, "password": "StaffPassword123!"})
    staff_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.post(f"/api/v1/purchase-orders/{order['id']}/submit", headers=staff_headers).status_code == 403
    assert client.get("/api/v1/purchase-orders", headers=staff_headers).status_code == 200

    other_token = register_user(client, "purchase_other_org")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/purchase-orders/{order['id']}", headers=other_headers).status_code == 404
    cross_supplier = client.post(
        "/api/v1/suppliers",
        json={"name": "Other Supplier"},
        headers=other_headers,
    )
    other_supplier = cross_supplier.json()
    invalid = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": other_supplier["id"],
            "branch_id": branch["id"],
            "items": [{"product_id": product["id"], "quantity": "1", "unit_cost": "1.00"}],
        },
        headers=admin_headers,
    )
    assert invalid.status_code == 400


def test_procurement_analytics_summary():
    client = TestClient(app)
    token = register_user(client, "purchase_analytics")
    headers = {"Authorization": f"Bearer {token}"}
    branch, supplier, product = setup_procurement_data(client, headers)
    create_po(client, headers, branch, supplier, product)

    response = client.get("/api/v1/analytics/procurement", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["purchase_order_count"] == 1
    assert data["pending_approvals"] == 0
    assert Decimal(data["purchasing_total"]) == Decimal("103.00")
    assert data["top_suppliers"][0]["supplier_name"] == "Procurement Supplier"
