from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email(prefix: str = "supplier") -> str:
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def register_user(client: TestClient, prefix: str = "sup_org"):
    email = _unique_email(prefix)
    payload = {
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Supplier User",
        "organization_name": "Supplier Organization",
        "organization_slug": f"supplier-org-{uuid4().hex[:8]}",
    }
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"]


def test_suppliers_crud_and_isolation():
    client = TestClient(app)
    token1 = register_user(client, "org1")
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 1. Create Supplier
    supplier_payload = {
        "name": "Acme Supplier",
        "email": "acme@example.com",
        "phone": "123-456-7890",
        "address": "123 Supply Road",
        "notes": "Primary packaging supplier",
    }
    resp = client.post("/api/v1/suppliers", json=supplier_payload, headers=headers1)
    assert resp.status_code == 200, resp.text
    supplier = resp.json()
    assert supplier["name"] == "Acme Supplier"
    assert supplier["is_active"] is True
    supplier_id = supplier["id"]

    # 2. Get Supplier Details
    resp = client.get(f"/api/v1/suppliers/{supplier_id}", headers=headers1)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme Supplier"

    # 3. List Suppliers (with search)
    resp = client.get("/api/v1/suppliers?q=Acme", headers=headers1)
    assert resp.status_code == 200
    suppliers = resp.json()
    assert any(s["id"] == supplier_id for s in suppliers)

    # 4. Update Supplier
    resp = client.patch(
        f"/api/v1/suppliers/{supplier_id}",
        json={"name": "Acme Supplier Updated", "phone": "000-000-0000"},
        headers=headers1,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme Supplier Updated"
    assert resp.json()["phone"] == "000-000-0000"

    # 5. Tenant Isolation: Create user in Org 2 and try to access Org 1's supplier
    token2 = register_user(client, "org2")
    headers2 = {"Authorization": f"Bearer {token2}"}

    resp = client.get(f"/api/v1/suppliers/{supplier_id}", headers=headers2)
    assert resp.status_code == 404

    resp = client.patch(
        f"/api/v1/suppliers/{supplier_id}",
        json={"name": "Hacked name"},
        headers=headers2,
    )
    assert resp.status_code == 404

    resp = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=headers2)
    assert resp.status_code == 404

    # 6. Soft Delete (Deactivate)
    resp = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=headers1)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # Fetching supplier should show is_active is now False
    resp = client.get(f"/api/v1/suppliers/{supplier_id}", headers=headers1)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_supplier_rbac():
    client = TestClient(app)
    
    # Register admin user to get credentials
    admin_token = register_user(client, "rbac_admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Add a staff member to the organization
    staff_email = _unique_email("rbac_staff")
    add_member_payload = {
        "email": staff_email,
        "password": "StaffPassword123!",
        "full_name": "Staff Member",
        "role_name": "staff",
    }
    resp = client.post("/api/v1/organization/members", json=add_member_payload, headers=admin_headers)
    assert resp.status_code == 200, resp.text

    # Login as staff member
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": staff_email, "password": "StaffPassword123!"},
    )
    assert login_resp.status_code == 200, login_resp.text
    staff_token = login_resp.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # Staff should NOT be able to create a supplier
    resp = client.post(
        "/api/v1/suppliers",
        json={"name": "Staff Supplier"},
        headers=staff_headers,
    )
    assert resp.status_code == 403

    # Admin creates a supplier
    resp = client.post(
        "/api/v1/suppliers",
        json={"name": "Admin Supplier"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    supplier_id = resp.json()["id"]

    # Staff should be able to VIEW the supplier
    resp = client.get(f"/api/v1/suppliers/{supplier_id}", headers=staff_headers)
    assert resp.status_code == 200

    # Staff should NOT be able to UPDATE the supplier
    resp = client.patch(
        f"/api/v1/suppliers/{supplier_id}",
        json={"name": "Staff updated supplier name"},
        headers=staff_headers,
    )
    assert resp.status_code == 403

    # Staff should NOT be able to DELETE the supplier
    resp = client.delete(f"/api/v1/suppliers/{supplier_id}", headers=staff_headers)
    assert resp.status_code == 403


def test_supplier_product_relationship():
    client = TestClient(app)
    admin_token = register_user(client, "rel_admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create supplier
    resp = client.post(
        "/api/v1/suppliers",
        json={"name": "Relation Supplier"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    supplier_id = resp.json()["id"]

    # Create product linked to supplier
    product_payload = {
        "sku": f"SKU-{uuid4().hex[:6]}",
        "name": "Linked Product",
        "unit": "box",
        "cost_price": 10.0,
        "selling_price": 20.0,
        "tax_rate": 0.05,
        "supplier_id": supplier_id,
    }
    resp = client.post("/api/v1/products", json=product_payload, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    product = resp.json()
    assert product["supplier_id"] == supplier_id

    # Get product and verify relationship
    resp = client.get(f"/api/v1/products/{product['id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["supplier_id"] == supplier_id

    # Create product with INVALID supplier_id -> should fail
    product_payload_invalid = {
        "sku": f"SKU-{uuid4().hex[:6]}",
        "name": "Invalid Product",
        "unit": "box",
        "cost_price": 10.0,
        "selling_price": 20.0,
        "tax_rate": 0.05,
        "supplier_id": str(uuid4()),
    }
    resp = client.post("/api/v1/products", json=product_payload_invalid, headers=admin_headers)
    assert resp.status_code == 400
