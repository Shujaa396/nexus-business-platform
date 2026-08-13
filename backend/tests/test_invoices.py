from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email(prefix: str = "inv_user") -> str:
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def register_user(client: TestClient, prefix: str = "inv"):
    email = _unique_email(prefix)
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Invoice User",
        "organization_name": f"Org {prefix}",
        "organization_slug": f"org-{prefix}-{uuid4().hex[:8]}",
    }
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def setup_branch_product_customer(client: TestClient, headers: dict):
    # Branch
    r = client.post("/api/v1/branches", json={"code": f"B-{uuid4().hex[:4]}", "name": "Main Branch"}, headers=headers)
    assert r.status_code == 200, r.text
    branch_id = r.json()["id"]

    # Customer
    r = client.post("/api/v1/customers", json={"name": "Acme Corp", "email": "acme@example.com"}, headers=headers)
    assert r.status_code == 200, r.text
    customer_id = r.json()["id"]

    # Product
    prod_payload = {
        "sku": f"SKU-{uuid4().hex[:6]}",
        "name": "Super Widget",
        "description": "High quality widget",
        "unit": "pcs",
        "cost_price": "50.00",
        "selling_price": "100.00",
        "tax_rate": "0.10",
        "category_id": None,
    }
    r = client.post("/api/v1/products", json=prod_payload, headers=headers)
    assert r.status_code == 200, r.text
    product_id = r.json()["id"]

    # Stock in
    r = client.post(
        "/api/v1/inventory/stock-in",
        json={"branch_id": branch_id, "product_id": product_id, "quantity": "50"},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    return branch_id, customer_id, product_id


def create_and_confirm_order(client: TestClient, headers: dict, branch_id: str, product_id: str, customer_id: str = None):
    order_payload = {
        "branch_id": branch_id,
        "customer_id": customer_id,
        "items": [
            {
                "product_id": product_id,
                "quantity": "2",
                "unit_price": "100.00",
                "discount": "10.00",
                "tax": "19.00",
            }
        ],
        "notes": "Test Order",
    }
    r = client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert r.status_code == 200, r.text
    order = r.json()
    order_id = order["id"]

    # Confirm order
    r = client.post(f"/api/v1/orders/{order_id}/confirm", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_generate_invoice_from_confirmed_order():
    client = TestClient(app)
    token = register_user(client, "gen_inv")
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, customer_id, product_id = setup_branch_product_customer(client, headers)

    order = create_and_confirm_order(client, headers, branch_id, product_id, customer_id)
    order_id = order["id"]

    # Generate invoice
    r = client.post("/api/v1/invoices", json={"order_id": order_id, "notes": "Initial invoice"}, headers=headers)
    assert r.status_code == 201, r.text
    inv = r.json()

    assert inv["order_id"] == order_id
    assert inv["status"] == "DRAFT"
    assert inv["invoice_number"].startswith("INV-")
    assert Decimal(str(inv["subtotal"])) == Decimal("200.00")
    assert Decimal(str(inv["discount"])) == Decimal("10.00")
    assert Decimal(str(inv["tax"])) == Decimal("19.00")
    assert Decimal(str(inv["total"])) == Decimal("209.00")
    assert len(inv["line_items"]) == 1
    assert inv["line_items"][0]["product_name"] == "Super Widget"


def test_cannot_generate_invoice_for_draft_order():
    client = TestClient(app)
    token = register_user(client, "draft_order_inv")
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, _, product_id = setup_branch_product_customer(client, headers)

    # Create order without confirming
    order_payload = {
        "branch_id": branch_id,
        "items": [{"product_id": product_id, "quantity": "1", "unit_price": "100.00"}],
    }
    r = client.post("/api/v1/orders", json=order_payload, headers=headers)
    order_id = r.json()["id"]

    r = client.post("/api/v1/invoices", json={"order_id": order_id}, headers=headers)
    assert r.status_code == 400
    assert "CONFIRMED" in r.json()["detail"]


def test_cannot_generate_duplicate_invoice():
    client = TestClient(app)
    token = register_user(client, "dup_inv")
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, _, product_id = setup_branch_product_customer(client, headers)
    order = create_and_confirm_order(client, headers, branch_id, product_id)
    order_id = order["id"]

    # First invoice succeeds
    r1 = client.post("/api/v1/invoices", json={"order_id": order_id}, headers=headers)
    assert r1.status_code == 201

    # Second invoice fails
    r2 = client.post("/api/v1/invoices", json={"order_id": order_id}, headers=headers)
    assert r2.status_code == 400
    assert "already been generated" in r2.json()["detail"]


def test_invoice_lifecycle_and_payments():
    client = TestClient(app)
    token = register_user(client, "lifecycle_inv")
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, _, product_id = setup_branch_product_customer(client, headers)
    order = create_and_confirm_order(client, headers, branch_id, product_id)
    order_id = order["id"]

    # 1. Generate Invoice (DRAFT)
    r = client.post("/api/v1/invoices", json={"order_id": order_id}, headers=headers)
    inv_id = r.json()["id"]
    assert r.json()["status"] == "DRAFT"

    # Cannot pay DRAFT invoice
    r_pay_draft = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": "100.00", "payment_method": "CASH"},
        headers=headers,
    )
    assert r_pay_draft.status_code == 400

    # 2. Issue Invoice (DRAFT -> ISSUED)
    r_issue = client.post(f"/api/v1/invoices/{inv_id}/issue", json={}, headers=headers)
    assert r_issue.status_code == 200
    assert r_issue.json()["status"] == "ISSUED"

    # Cannot issue already ISSUED invoice
    r_reissue = client.post(f"/api/v1/invoices/{inv_id}/issue", json={}, headers=headers)
    assert r_reissue.status_code == 400

    # 3. Partial Payment (ISSUED -> PARTIAL)
    r_pay1 = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": "100.00", "payment_method": "CARD", "reference": "REF123"},
        headers=headers,
    )
    assert r_pay1.status_code == 200

    # Retrieve invoice to verify PARTIAL status
    r_get = client.get(f"/api/v1/invoices/{inv_id}", headers=headers)
    assert r_get.status_code == 200
    assert r_get.json()["status"] == "PARTIAL"
    assert Decimal(str(r_get.json()["amount_paid"])) == Decimal("100.00")

    # 4. Final Payment (PARTIAL -> PAID)
    remaining = Decimal("209.00") - Decimal("100.00")
    r_pay2 = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": str(remaining), "payment_method": "CASH"},
        headers=headers,
    )
    assert r_pay2.status_code == 200

    r_get_paid = client.get(f"/api/v1/invoices/{inv_id}", headers=headers)
    assert r_get_paid.json()["status"] == "PAID"
    assert Decimal(str(r_get_paid.json()["amount_paid"])) == Decimal("209.00")

    # 5. Overpayment prevention
    r_overpay = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": "10.00", "payment_method": "CASH"},
        headers=headers,
    )
    assert r_overpay.status_code == 400


def test_void_invoice():
    client = TestClient(app)
    token = register_user(client, "void_inv")
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, _, product_id = setup_branch_product_customer(client, headers)
    order = create_and_confirm_order(client, headers, branch_id, product_id)
    order_id = order["id"]

    r = client.post("/api/v1/invoices", json={"order_id": order_id}, headers=headers)
    inv_id = r.json()["id"]

    # Issue invoice
    client.post(f"/api/v1/invoices/{inv_id}/issue", headers=headers)

    # Void invoice
    r_void = client.post(f"/api/v1/invoices/{inv_id}/void", json={"notes": "Customer cancelled"}, headers=headers)
    assert r_void.status_code == 200
    assert r_void.json()["status"] == "VOID"

    # Cannot pay voided invoice
    r_pay = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": "50.00", "payment_method": "CASH"},
        headers=headers,
    )
    assert r_pay.status_code == 400


def test_tenant_isolation_on_invoices():
    client = TestClient(app)
    token1 = register_user(client, "tenant1_inv")
    headers1 = {"Authorization": f"Bearer {token1}"}

    token2 = register_user(client, "tenant2_inv")
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Org 1 creates order and invoice
    branch_id, _, product_id = setup_branch_product_customer(client, headers1)
    order = create_and_confirm_order(client, headers1, branch_id, product_id)
    r_inv = client.post("/api/v1/invoices", json={"order_id": order["id"]}, headers=headers1)
    inv_id = r_inv.json()["id"]

    # Org 2 tries to retrieve Org 1's invoice -> 404
    r_get2 = client.get(f"/api/v1/invoices/{inv_id}", headers=headers2)
    assert r_get2.status_code == 404

    # Org 2 tries to issue Org 1's invoice -> 404
    r_issue2 = client.post(f"/api/v1/invoices/{inv_id}/issue", headers=headers2)
    assert r_issue2.status_code == 404

    # Org 2 list invoices -> does not include Org 1's invoice
    r_list2 = client.get("/api/v1/invoices", headers=headers2)
    assert r_list2.status_code == 200
    ids = [i["id"] for i in r_list2.json()]
    assert inv_id not in ids
