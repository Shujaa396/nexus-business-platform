from fastapi import APIRouter

from app.api.v1.routes import auth, health
from app.api.v1.routes import inventory, products, categories, branches, customers, orders, payments

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
from app.api.v1.routes import inventory

api_router.include_router(inventory.router)
api_router.include_router(products.router)
api_router.include_router(categories.router)
api_router.include_router(branches.router)
api_router.include_router(customers.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
