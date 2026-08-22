from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_engine, get_session_factory
from app.main import app
from app.models import (
    InventoryItem,
    InventoryTransaction,
    Payment,
    PurchaseReceipt,
    WarehouseInventory,
)
from tests.test_dashboard import register_user
from tests.test_purchase_orders import create_po, setup_procurement_data
from tests.test_sales_orders import progress_order, setup_sales_data


def _concurrent_posts(path: str, payload: dict, headers: dict[str, str]) -> list:
    def submit() -> object:
        with TestClient(app) as client:
            return client.post(path, json=payload, headers=headers)

    with ThreadPoolExecutor(max_workers=2) as executor:
        return list(executor.map(lambda _index: submit(), range(2)))


def _require_postgres() -> None:
    try:
        engine = get_engine()
    except RuntimeError:
        pytest.skip("Concurrent row-lock behavior requires PostgreSQL")
    if engine.dialect.name != "postgresql":
        pytest.skip("Concurrent row-lock behavior requires PostgreSQL")
    engine.dispose()


def test_concurrent_duplicate_purchase_receipt_is_single_movement():
    _require_postgres()
    setup_client = TestClient(app)
    token = register_user(setup_client, "receipt_concurrency")
    headers = {"Authorization": f"Bearer {token}"}
    branch, supplier, product = setup_procurement_data(setup_client, headers)
    order = create_po(setup_client, headers, branch, supplier, product, "10")
    assert (
        setup_client.post(
            f"/api/v1/purchase-orders/{order['id']}/submit", headers=headers
        ).status_code
        == 200
    )
    assert (
        setup_client.post(
            f"/api/v1/purchase-orders/{order['id']}/approve", headers=headers
        ).status_code
        == 200
    )
    payload = {
        "receipt_reference": "CONCURRENT-GRN",
        "idempotency_key": "CONCURRENT-RECEIPT-1",
        "items": [{"item_id": order["items"][0]["id"], "quantity": "10"}],
    }

    responses = _concurrent_posts(
        f"/api/v1/purchase-orders/{order['id']}/receive", payload, headers
    )

    assert sorted(response.status_code for response in responses) == [200, 200]
    session = get_session_factory()()
    try:
        receipts = (
            session.query(PurchaseReceipt)
            .filter(
                PurchaseReceipt.organization_id == order["organization_id"],
                PurchaseReceipt.idempotency_key == payload["idempotency_key"],
            )
            .all()
        )
        movements = (
            session.query(InventoryTransaction)
            .filter(
                InventoryTransaction.organization_id == order["organization_id"],
                InventoryTransaction.reference_type == "PURCHASE_ORDER_RECEIPT",
                InventoryTransaction.reference_id == order["id"],
            )
            .all()
        )
        inventory = (
            session.query(InventoryItem)
            .filter(
                InventoryItem.organization_id == order["organization_id"],
                InventoryItem.product_id == product["id"],
            )
            .one()
        )
        assert len(receipts) == 1
        assert len(movements) == 1
        assert inventory.quantity == Decimal("10")
    finally:
        session.close()


def test_concurrent_refunds_allow_only_one_refund():
    _require_postgres()
    setup_client = TestClient(app)
    token = register_user(setup_client, "refund_concurrency")
    headers = {"Authorization": f"Bearer {token}"}
    branch, warehouse, customer, product = setup_sales_data(setup_client, headers)
    order_response = setup_client.post(
        "/api/v1/sales-orders",
        json={
            "branch_id": branch["id"],
            "warehouse_id": warehouse["id"],
            "items": [{"product_id": product["id"], "quantity": "4"}],
        },
        headers=headers,
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    progress_order(setup_client, headers, order)
    fulfilled = setup_client.post(
        f"/api/v1/sales-orders/{order['id']}/fulfill",
        json={"items": [{"item_id": order["items"][0]["id"], "quantity": "4"}]},
        headers=headers,
    )
    assert fulfilled.status_code == 200
    invoice = setup_client.post(f"/api/v1/sales-orders/{order['id']}/invoice", headers=headers)
    assert invoice.status_code == 200
    invoice_id = invoice.json()["id"]
    assert (
        setup_client.post(f"/api/v1/invoices/{invoice_id}/issue", headers=headers).status_code
        == 200
    )
    payment = setup_client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": "100.00", "payment_method": "CASH"},
        headers=headers,
    )
    assert payment.status_code == 200
    payment_id = payment.json()["id"]

    responses = _concurrent_posts(f"/api/v1/payments/{payment_id}/refund", {}, headers)

    assert sorted(response.status_code for response in responses) == [200, 400]
    session = get_session_factory()()
    try:
        persisted = session.get(Payment, payment_id)
        assert persisted is not None
        assert persisted.status == "REFUNDED"
        assert persisted.amount == Decimal("100")
    finally:
        session.close()


def test_concurrent_fulfillment_consumes_reserved_quantity_once():
    _require_postgres()
    setup_client = TestClient(app)
    token = register_user(setup_client, "fulfillment_concurrency")
    headers = {"Authorization": f"Bearer {token}"}
    branch, warehouse, customer, product = setup_sales_data(setup_client, headers)
    order_response = setup_client.post(
        "/api/v1/sales-orders",
        json={
            "branch_id": branch["id"],
            "warehouse_id": warehouse["id"],
            "items": [{"product_id": product["id"], "quantity": "4"}],
        },
        headers=headers,
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    progress_order(setup_client, headers, order)
    payload = {"items": [{"item_id": order["items"][0]["id"], "quantity": "4"}]}

    responses = _concurrent_posts(f"/api/v1/sales-orders/{order['id']}/fulfill", payload, headers)

    assert sorted(response.status_code for response in responses) == [200, 400]
    session = get_session_factory()()
    try:
        inventory = (
            session.query(WarehouseInventory)
            .filter(
                WarehouseInventory.organization_id == order["organization_id"],
                WarehouseInventory.warehouse_id == warehouse["id"],
                WarehouseInventory.product_id == product["id"],
            )
            .one()
        )
        movements = (
            session.query(InventoryTransaction)
            .filter(
                InventoryTransaction.organization_id == order["organization_id"],
                InventoryTransaction.transaction_type == "SALE",
                InventoryTransaction.reference_id == order["id"],
            )
            .all()
        )
        assert inventory.quantity == Decimal("6")
        assert inventory.reserved_quantity == Decimal("0")
        assert len(movements) == 1
    finally:
        session.close()
