from fastapi import APIRouter

from app.api.v1.routes import (
    analytics,
    audit_logs,
    auth,
    branches,
    categories,
    customers,
    dashboard,
    health,
    inventory,
    invoices,
    orders,
    organization,
    payments,
    products,
    purchase_orders,
    suppliers,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)

api_router.include_router(organization.router)
api_router.include_router(audit_logs.router)
api_router.include_router(inventory.router)
api_router.include_router(products.router)
api_router.include_router(categories.router)
api_router.include_router(branches.router)
api_router.include_router(customers.router)
api_router.include_router(suppliers.router)
api_router.include_router(purchase_orders.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(invoices.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
