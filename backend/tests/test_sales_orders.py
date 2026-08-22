from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.test_dashboard import register_user


def setup_sales_data(client: TestClient, headers: dict[str, str]):
    branch = client.post("/api/v1/branches", json={"code": f"SO-{uuid4().hex[:6]}", "name": "Sales Branch"}, headers=headers)
    assert branch.status_code == 200, branch.text
    warehouse = client.post("/api/v1/warehouses", json={"name": "Sales Warehouse", "code": f"SW-{uuid4().hex[:6]}", "branch_id": branch.json()["id"]}, headers=headers)
    assert warehouse.status_code == 201, warehouse.text
    customer = client.post("/api/v1/customers", json={"name": "Sales Customer", "email": f"customer-{uuid4().hex[:6]}@example.com"}, headers=headers)
    assert customer.status_code == 200, customer.text
    product = client.post("/api/v1/products", json={"sku": f"SO-SKU-{uuid4().hex[:6]}", "name": "Sales Product", "unit": "unit", "cost_price": "5.00", "selling_price": "25.00", "tax_rate": "0"}, headers=headers)
    assert product.status_code == 200, product.text
    stock = client.post("/api/v1/inventory/adjustments", json={"warehouse_id": warehouse.json()["id"], "product_id": product.json()["id"], "quantity": "10", "reason": "Sales stock"}, headers=headers)
    assert stock.status_code == 200, stock.text
    return branch.json(), warehouse.json(), customer.json(), product.json()


def create_sales_order(client: TestClient, headers: dict[str, str], branch: dict, warehouse: dict, customer: dict, product: dict, quantity: str = "4"):
    response = client.post("/api/v1/sales-orders", json={"customer_id": customer["id"], "branch_id": branch["id"], "warehouse_id": warehouse["id"], "items": [{"product_id": product["id"], "quantity": quantity, "unit_price": "1.00"}]}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def progress_order(client: TestClient, headers: dict[str, str], order: dict):
    order_id = order["id"]
    for action in ("submit", "approve", "reserve"):
        response = client.post(f"/api/v1/sales-orders/{order_id}/{action}", headers=headers)
        assert response.status_code == 200, response.text
    return order_id


def test_sales_order_reservation_fulfillment_invoice_and_payment():
    client = TestClient(app)
    token = register_user(client, "sales_lifecycle")
    headers = {"Authorization": f"Bearer {token}"}
    branch, warehouse, customer, product = setup_sales_data(client, headers)
    order = create_sales_order(client, headers, branch, warehouse, customer, product)
    assert Decimal(order["total"]) == Decimal("100.0000")
    order_id = progress_order(client, headers, order)

    inventory = client.get(f"/api/v1/inventory/by-warehouse?warehouse_id={warehouse['id']}", headers=headers).json()[0]
    assert Decimal(inventory["reserved_quantity"]) == Decimal("4")
    partial = client.post(f"/api/v1/sales-orders/{order_id}/fulfill", json={"items": [{"item_id": order["items"][0]["id"], "quantity": "2"}]}, headers=headers)
    assert partial.status_code == 200, partial.text
    assert partial.json()["status"] == "PARTIALLY_FULFILLED"

    duplicate = client.post(f"/api/v1/sales-orders/{order_id}/fulfill", json={"items": [{"item_id": order["items"][0]["id"], "quantity": "3"}]}, headers=headers)
    assert duplicate.status_code == 400
    complete = client.post(f"/api/v1/sales-orders/{order_id}/fulfill", json={"items": [{"item_id": order["items"][0]["id"], "quantity": "2"}]}, headers=headers)
    assert complete.status_code == 200
    assert complete.json()["status"] == "FULFILLED"

    warehouse_stock = client.get(f"/api/v1/inventory/by-warehouse?warehouse_id={warehouse['id']}", headers=headers).json()[0]
    assert Decimal(warehouse_stock["quantity"]) == Decimal("6")
    assert Decimal(warehouse_stock["reserved_quantity"]) == Decimal("0")

    invoice = client.post(f"/api/v1/sales-orders/{order_id}/invoice", headers=headers)
    assert invoice.status_code == 200, invoice.text
    assert invoice.json()["order_id"] == order_id
    paid = client.post(f"/api/v1/invoices/{invoice.json()['id']}/issue", headers=headers)
    assert paid.status_code == 200
    payment = client.post(f"/api/v1/invoices/{invoice.json()['id']}/payments", json={"amount": "100.00", "payment_method": "CASH"}, headers=headers)
    assert payment.status_code == 200, payment.text

    history = client.get(f"/api/v1/sales-orders/customers/{customer['id']}/sales-orders", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["id"] == order_id
    audit = client.get("/api/v1/audit-logs?entity_type=SALES_ORDER", headers=headers)
    assert audit.status_code == 200
    assert {entry["action"] for entry in audit.json()} >= {"SALES_ORDER_CREATED", "SALES_ORDER_RESERVED", "SALES_ORDER_FULFILLED", "SALES_ORDER_INVOICED"}


def test_sales_order_validation_rbac_and_tenant_isolation():
    client = TestClient(app)
    admin_token = register_user(client, "sales_admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    branch, warehouse, customer, product = setup_sales_data(client, admin_headers)
    order = create_sales_order(client, admin_headers, branch, warehouse, customer, product)

    invalid = client.post("/api/v1/sales-orders", json={"customer_id": str(uuid4()), "branch_id": branch["id"], "warehouse_id": warehouse["id"], "items": [{"product_id": product["id"], "quantity": "1"}]}, headers=admin_headers)
    assert invalid.status_code == 400
    unauthenticated = client.get("/api/v1/sales-orders")
    assert unauthenticated.status_code == 401

    staff_email = f"sales_staff_{uuid4().hex[:8]}@example.com"
    member = client.post("/api/v1/organization/members", json={"email": staff_email, "password": "StaffPassword123!", "full_name": "Sales Staff", "role_name": "staff"}, headers=admin_headers)
    assert member.status_code == 200
    login = client.post("/api/v1/auth/login", json={"email": staff_email, "password": "StaffPassword123!"})
    staff_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.post(f"/api/v1/sales-orders/{order['id']}/approve", headers=staff_headers).status_code == 403
    assert client.post(f"/api/v1/sales-orders/{order['id']}/submit", headers=staff_headers).status_code == 200

    other_token = register_user(client, "sales_other")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/sales-orders/{order['id']}", headers=other_headers).status_code == 404
    assert client.get(f"/api/v1/sales-orders/customers/{customer['id']}/sales-orders", headers=other_headers).json() == []


def test_sales_order_explicit_confirmed_paid_and_completed_flow():
    client = TestClient(app)
    token = register_user(client, "sales_confirmed_paid")
    headers = {"Authorization": f"Bearer {token}"}
    branch, warehouse, customer, product = setup_sales_data(client, headers)
    order = create_sales_order(client, headers, branch, warehouse, customer, product)

    confirm = client.post(f"/api/v1/sales-orders/{order['id']}/confirm", headers=headers)
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["status"] == "CONFIRMED"

    reserve = client.post(f"/api/v1/sales-orders/{order['id']}/reserve", headers=headers)
    assert reserve.status_code == 200, reserve.text
    assert reserve.json()["status"] == "RESERVED"

    fulfill = client.post(f"/api/v1/sales-orders/{order['id']}/fulfill", json={"items": [{"item_id": order["items"][0]["id"], "quantity": "4"}]}, headers=headers)
    assert fulfill.status_code == 200, fulfill.text
    assert fulfill.json()["status"] == "FULFILLED"

    invoice = client.post(f"/api/v1/sales-orders/{order['id']}/invoice", headers=headers)
    assert invoice.status_code == 200, invoice.text
    invoice_id = invoice.json()["id"]

    issued = client.post(f"/api/v1/invoices/{invoice_id}/issue", headers=headers)
    assert issued.status_code == 200, issued.text

    payment = client.post(f"/api/v1/invoices/{invoice_id}/payments", json={"amount": "100.00", "payment_method": "CASH"}, headers=headers)
    assert payment.status_code == 200, payment.text

    mark_paid = client.post(f"/api/v1/sales-orders/{order['id']}/paid", headers=headers)
    assert mark_paid.status_code == 200, mark_paid.text
    assert mark_paid.json()["status"] == "PAID"

    complete = client.post(f"/api/v1/sales-orders/{order['id']}/complete", headers=headers)
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "COMPLETED"

    duplicate_complete = client.post(f"/api/v1/sales-orders/{order['id']}/complete", headers=headers)
    assert duplicate_complete.status_code == 400, duplicate_complete.text


def test_sales_order_cancellation_releases_reservation_and_invalid_transitions():
    client = TestClient(app)
    token = register_user(client, "sales_cancel")
    headers = {"Authorization": f"Bearer {token}"}
    branch, warehouse, customer, product = setup_sales_data(client, headers)
    order = create_sales_order(client, headers, branch, warehouse, customer, product)
    order_id = progress_order(client, headers, order)
    cancelled = client.post(f"/api/v1/sales-orders/{order_id}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"
    stock = client.get(f"/api/v1/inventory/by-warehouse?warehouse_id={warehouse['id']}", headers=headers).json()[0]
    assert Decimal(stock["reserved_quantity"]) == Decimal("0")
    assert client.post(f"/api/v1/sales-orders/{order_id}/reserve", headers=headers).status_code == 400
