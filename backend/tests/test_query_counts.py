from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event

from app.db import session as session_module
from app.main import app
from tests.test_dashboard import register_user
from tests.test_purchase_orders import create_po, setup_procurement_data
from tests.test_sales_orders import setup_sales_data


def test_staff_order_detail_uses_bounded_queries(monkeypatch):
    engine = create_engine("sqlite:///./test.db", pool_pre_ping=True, future=True)
    monkeypatch.setattr(session_module, "get_engine", lambda: engine)
    statements: list[str] = []

    def count_statement(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", count_statement)
    try:
        client = TestClient(app)
        token = register_user(client, "query_count_order")
        headers = {"Authorization": f"Bearer {token}"}
        branch, warehouse, customer, product = setup_sales_data(client, headers)
        extra_products = []
        for index in range(2):
            response = client.post(
                "/api/v1/products",
                json={
                    "sku": f"QUERY-{uuid4().hex[:8]}",
                    "name": f"Query Product {index}",
                    "unit": "unit",
                    "cost_price": "1.00",
                    "selling_price": "2.00",
                    "tax_rate": "0",
                },
                headers=headers,
            )
            assert response.status_code == 200, response.text
            extra_products.append(response.json())
        order = client.post(
            "/api/v1/sales-orders",
            json={
                "customer_id": customer["id"],
                "branch_id": branch["id"],
                "warehouse_id": warehouse["id"],
                "items": [
                    {"product_id": product["id"], "quantity": "1"},
                    *[{"product_id": item["id"], "quantity": "1"} for item in extra_products],
                ],
            },
            headers=headers,
        )
        assert order.status_code == 201, order.text
        statements.clear()

        response = client.get(f"/api/v1/orders/{order.json()['id']}", headers=headers)
        assert response.status_code == 200, response.text
        assert len(response.json()["items"]) == 3
        assert len(statements) <= 8
    finally:
        event.remove(engine, "before_cursor_execute", count_statement)
        engine.dispose()


def test_high_risk_detail_paths_use_bounded_queries(monkeypatch):
    engine = create_engine("sqlite:///./test.db", pool_pre_ping=True, future=True)
    monkeypatch.setattr(session_module, "get_engine", lambda: engine)
    statements: list[str] = []

    def count_statement(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", count_statement)
    try:
        client = TestClient(app)
        token = register_user(client, "query_count_details")
        headers = {"Authorization": f"Bearer {token}"}
        branch, warehouse, customer, product = setup_sales_data(client, headers)
        stock_in = client.post(
            "/api/v1/inventory/stock-in",
            json={"branch_id": branch["id"], "product_id": product["id"], "quantity": "2"},
            headers=headers,
        )
        assert stock_in.status_code == 200, stock_in.text
        account_email = f"query-portal-{uuid4().hex[:8]}@example.com"
        account = client.post(
            f"/api/v1/customers/{customer['id']}/account",
            json={"email": account_email, "password": "CustomerPass123!"},
            headers=headers,
        )
        assert account.status_code == 200, account.text
        portal_login = client.post(
            "/api/v1/auth/login",
            json={"email": account_email, "password": "CustomerPass123!"},
        )
        assert portal_login.status_code == 200, portal_login.text
        portal_headers = {"Authorization": f"Bearer {portal_login.json()['access_token']}"}

        customer_order = client.post(
            "/api/v1/orders",
            json={
                "branch_id": branch["id"],
                "customer_id": customer["id"],
                "items": [{"product_id": product["id"], "quantity": "1"}],
            },
            headers=headers,
        )
        assert customer_order.status_code == 200, customer_order.text
        customer_order_data = customer_order.json()
        customer_order_id = customer_order_data["id"]
        confirmed = client.post(f"/api/v1/orders/{customer_order_id}/confirm", headers=headers)
        assert confirmed.status_code == 200, confirmed.text
        customer_invoice = client.post(
            "/api/v1/invoices",
            json={"order_id": customer_order_id},
            headers=headers,
        )
        assert customer_invoice.status_code == 201, customer_invoice.text

        order = client.post(
            "/api/v1/sales-orders",
            json={
                "branch_id": branch["id"],
                "warehouse_id": warehouse["id"],
                "items": [{"product_id": product["id"], "quantity": "1"}],
            },
            headers=headers,
        )
        assert order.status_code == 201, order.text
        order_id = order.json()["id"]
        order_data = order.json()
        for action in ("submit", "approve", "reserve"):
            transition = client.post(f"/api/v1/sales-orders/{order_id}/{action}", headers=headers)
            assert transition.status_code == 200, transition.text
        fulfillment = client.post(
            f"/api/v1/sales-orders/{order_id}/fulfill",
            json={"items": [{"item_id": order_data["items"][0]["id"], "quantity": "1"}]},
            headers=headers,
        )
        assert fulfillment.status_code == 200, fulfillment.text
        invoice = client.post(f"/api/v1/sales-orders/{order_id}/invoice", headers=headers)
        assert invoice.status_code == 200, invoice.text
        purchase_branch, supplier, purchase_product = setup_procurement_data(client, headers)
        purchase_order = create_po(
            client, headers, purchase_branch, supplier, purchase_product, "2"
        )

        checks = [
            (f"/api/v1/customers/{customer['id']}", headers, 4),
            ("/api/v1/customers/portal/me", portal_headers, 32),
            (f"/api/v1/orders/{order_id}", headers, 8),
            (f"/api/v1/purchase-orders/{purchase_order['id']}", headers, 8),
            (f"/api/v1/sales-orders/{order_id}", headers, 8),
            (f"/api/v1/invoices/{invoice.json()['id']}", headers, 8),
            (f"/api/v1/customers/portal/orders/{customer_order_id}", portal_headers, 8),
            (
                f"/api/v1/customers/portal/invoices/{customer_invoice.json()['id']}",
                portal_headers,
                12,
            ),
        ]
        for path, request_headers, limit in checks:
            statements.clear()
            response = client.get(path, headers=request_headers)
            assert response.status_code == 200, response.text
            assert len(statements) <= limit, f"{path} used {len(statements)} queries"

    finally:
        event.remove(engine, "before_cursor_execute", count_statement)
        engine.dispose()
