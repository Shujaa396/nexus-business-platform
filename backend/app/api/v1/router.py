from fastapi import APIRouter

from app.api.v1.routes import auth, health
from app.api.v1.routes import inventory, products, categories, branches

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
from app.api.v1.routes import inventory

api_router.include_router(inventory.router, prefix="/inventory")
api_router.include_router(products.router, prefix="/products")
api_router.include_router(categories.router, prefix="/categories")
api_router.include_router(branches.router, prefix="/branches")
