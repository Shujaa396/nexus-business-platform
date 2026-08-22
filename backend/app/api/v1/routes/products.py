from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_membership, require_role
from app.db.session import get_db
from app.models import Category, Product, Supplier
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.audit import log_activity

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse)
def create_product(payload: ProductCreate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    # validate category ownership
    if payload.category_id:
        cat = db.get(Category, payload.category_id)
        if cat is None or cat.organization_id != org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")

    # validate supplier ownership
    if payload.supplier_id:
        sup = db.get(Supplier, payload.supplier_id)
        if sup is None or sup.organization_id != org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid supplier")

    # unique SKU per org
    existing = db.query(Product).filter(Product.organization_id == org_id, Product.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    product = Product(
        organization_id=org_id,
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        unit=payload.unit,
        cost_price=payload.cost_price,
        selling_price=payload.selling_price,
        tax_rate=payload.tax_rate or 0,
        category_id=payload.category_id,
        supplier_id=payload.supplier_id,
        is_active=True,
    )
    db.add(product)
    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="PRODUCT_CREATED",
        entity_type="PRODUCT",
        entity_id=product.id,
        details=f"Created product {product.name} (SKU: {product.sku})",
    )
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=list[ProductResponse])
def list_products(page: int = Query(1), page_size: int = Query(20), q: str | None = Query(None), category_id: UUID | None = Query(None), membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    qry = db.query(Product).filter(Product.organization_id == org_id)
    if q:
        qry = qry.filter((Product.name.ilike(f"%{q}%")) | (Product.sku.ilike(f"%{q}%")))
    if category_id:
        qry = qry.filter(Product.category_id == category_id)
    items = qry.offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, membership=Depends(get_current_membership), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    product = db.get(Product, product_id)
    if product is None or product.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: UUID, payload: ProductUpdate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    product = db.get(Product, product_id)
    if product is None or product.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if payload.category_id:
        cat = db.get(Category, payload.category_id)
        if cat is None or cat.organization_id != org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")

    if payload.supplier_id:
        sup = db.get(Supplier, payload.supplier_id)
        if sup is None or sup.organization_id != org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid supplier")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.add(product)
    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="PRODUCT_UPDATED",
        entity_type="PRODUCT",
        entity_id=product.id,
        details=f"Updated product {product.name} (SKU: {product.sku})",
    )
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: UUID, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    org_id = membership.organization_id
    product = db.get(Product, product_id)
    if product is None or product.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    product.is_active = False
    db.add(product)
    log_activity(
        db,
        organization_id=org_id,
        user=membership.user,
        action="PRODUCT_DEACTIVATED",
        entity_type="PRODUCT",
        entity_id=product.id,
        details=f"Deactivated product {product.name} (SKU: {product.sku})",
    )
    db.commit()
    return {"status": "ok"}
