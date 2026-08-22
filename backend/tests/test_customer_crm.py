from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.test_dashboard import register_user


def customer_payload(code: str, email: str) -> dict:
    return {
        "customer_code": code,
        "name": "CRM Customer",
        "company_name": "CRM Company",
        "email": email,
        "phone": "+1 555 0100",
        "billing_address": "1 Billing Way",
        "shipping_address": "2 Shipping Way",
        "status": "PROSPECT",
        "credit_limit": "5000",
        "discount_percent": "10",
        "notes": "Priority account",
    }


def test_customer_crm_fields_search_and_duplicate_validation():
    client = TestClient(app)
    token = register_user(client, "crm_fields")
    headers = {"Authorization": f"Bearer {token}"}
    email = f"crm-{uuid4().hex[:8]}@example.com"
    created = client.post("/api/v1/customers", json=customer_payload("CRM-001", email), headers=headers)
    assert created.status_code == 200, created.text
    customer = created.json()
    assert customer["status"] == "PROSPECT"
    assert customer["billing_address"] == "1 Billing Way"
    assert Decimal(customer["credit_limit"]) == Decimal("5000")

    search = client.get("/api/v1/customers?q=CRM-001&status_filter=PROSPECT", headers=headers)
    assert search.status_code == 200
    assert [entry["id"] for entry in search.json()] == [customer["id"]]

    duplicate = client.post("/api/v1/customers", json=customer_payload("CRM-001", f"other-{email}"), headers=headers)
    assert duplicate.status_code == 409

    updated = client.patch(f"/api/v1/customers/{customer['id']}", json={"status": "ACTIVE", "is_active": True}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["status"] == "ACTIVE"


def test_customer_pagination_metadata_and_filters():
    client = TestClient(app)
    token = register_user(client, "crm_pagination")
    headers = {"Authorization": f"Bearer {token}"}
    for index in range(5):
        response = client.post("/api/v1/customers", json={"name": f"Paged Customer {index}", "status": "PROSPECT" if index == 4 else "ACTIVE"}, headers=headers)
        assert response.status_code == 200, response.text
    first = client.get("/api/v1/customers?page=1&page_size=2&paginated=true", headers=headers)
    assert first.status_code == 200
    assert first.json()["page"] == 1
    assert first.json()["page_size"] == 2
    assert first.json()["total"] == 5
    assert first.json()["total_pages"] == 3
    assert first.json()["has_next"] is True
    last = client.get("/api/v1/customers?page=1&page_size=2&paginated=true&status_filter=PROSPECT", headers=headers)
    assert last.json()["total"] == 1
    assert last.json()["has_next"] is False


def test_customer_account_portal_is_owned_and_deactivation_blocks_access():
    client = TestClient(app)
    admin_token = register_user(client, "crm_portal_admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    first = client.post(
        "/api/v1/customers",
        json=customer_payload("PORTAL-001", f"portal-{uuid4().hex[:8]}@example.com"),
        headers=admin_headers,
    ).json()
    account_email = f"account-{uuid4().hex[:8]}@example.com"
    account = client.post(
        f"/api/v1/customers/{first['id']}/account",
        json={"email": account_email, "password": "CustomerPass123!"},
        headers=admin_headers,
    )
    assert account.status_code == 200, account.text

    login = client.post("/api/v1/auth/login", json={"email": account_email, "password": "CustomerPass123!"})
    assert login.status_code == 200, login.text
    portal_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    portal = client.get("/api/v1/customers/portal/me", headers=portal_headers)
    assert portal.status_code == 200, portal.text
    assert portal.json()["customer"]["id"] == first["id"]
    assert portal.json()["summary"]["order_count"] == 0
    assert client.get("/api/v1/orders", headers=portal_headers).status_code == 403
    assert client.get("/api/v1/invoices", headers=portal_headers).status_code == 403
    assert client.get(f"/api/v1/customers/portal/orders/{uuid4()}", headers=portal_headers).status_code == 404
    assert client.get(f"/api/v1/customers/portal/invoices/{uuid4()}", headers=portal_headers).status_code == 404

    other_token = register_user(client, "crm_portal_other")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/customers/{first['id']}/summary", headers=other_headers).status_code == 404
    assert client.get("/api/v1/customers/portal/me", headers=other_headers).status_code == 403

    deactivated = client.delete(f"/api/v1/customers/{first['id']}", headers=admin_headers)
    assert deactivated.status_code == 200
    assert client.get("/api/v1/customers/portal/me", headers=portal_headers).status_code == 403


def test_customer_contacts_addresses_and_portal_payment_history():
    client = TestClient(app)
    token = register_user(client, "crm_children")
    headers = {"Authorization": f"Bearer {token}"}
    customer = client.post("/api/v1/customers", json=customer_payload("CHILD-001", f"child-{uuid4().hex[:8]}@example.com"), headers=headers).json()

    contact = client.post(f"/api/v1/customers/{customer['id']}/contacts", json={"name": "Primary Contact", "email": "primary@example.com", "job_title": "Buyer", "is_primary": True}, headers=headers)
    assert contact.status_code == 201, contact.text
    second_contact = client.post(f"/api/v1/customers/{customer['id']}/contacts", json={"name": "Backup Contact", "is_primary": True}, headers=headers)
    assert second_contact.status_code == 201, second_contact.text
    contacts = client.get(f"/api/v1/customers/{customer['id']}/contacts", headers=headers).json()
    assert contacts[0]["is_primary"] is True
    assert contacts[1]["is_primary"] is False
    paged_contacts = client.get(f"/api/v1/customers/{customer['id']}/contacts?paginated=true&page_size=1", headers=headers)
    assert paged_contacts.status_code == 200
    assert paged_contacts.json()["total"] == 2
    assert paged_contacts.json()["total_pages"] == 2
    updated_contact = client.patch(f"/api/v1/customers/{customer['id']}/contacts/{contacts[0]['id']}", json={"name": "Updated Contact", "is_primary": True}, headers=headers)
    assert updated_contact.status_code == 200, updated_contact.text
    deleted_contact = client.delete(f"/api/v1/customers/{customer['id']}/contacts/{contacts[1]['id']}", headers=headers)
    assert deleted_contact.status_code == 200, deleted_contact.text

    billing = client.post(f"/api/v1/customers/{customer['id']}/addresses", json={"address_type": "BILLING", "line1": "10 Billing Street", "city": "Austin", "is_primary": True}, headers=headers)
    assert billing.status_code == 201, billing.text
    shipping = client.post(f"/api/v1/customers/{customer['id']}/addresses", json={"address_type": "SHIPPING", "line1": "20 Shipping Street", "is_primary": True}, headers=headers)
    assert shipping.status_code == 201, shipping.text
    addresses = client.get(f"/api/v1/customers/{customer['id']}/addresses", headers=headers).json()
    assert {address["address_type"] for address in addresses} == {"BILLING", "SHIPPING"}
    updated_address = client.patch(f"/api/v1/customers/{customer['id']}/addresses/{billing.json()['id']}", json={"address_type": "BILLING", "line1": "Updated Billing", "is_primary": True}, headers=headers)
    assert updated_address.status_code == 200, updated_address.text
    deleted_address = client.delete(f"/api/v1/customers/{customer['id']}/addresses/{shipping.json()['id']}", headers=headers)
    assert deleted_address.status_code == 200, deleted_address.text

    other_token = register_user(client, "crm_children_other")
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/v1/customers/{customer['id']}/contacts", headers=other_headers).status_code == 404
    assert client.get(f"/api/v1/customers/{customer['id']}/addresses", headers=other_headers).status_code == 404