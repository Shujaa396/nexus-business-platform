from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_current_user, hash_password, require_role
from app.db.session import get_db
from app.models import Customer, Invoice, Order, OrderItem, OrganizationMembership, Role, User
from app.schemas.auth import UserPublic
from app.schemas.customers import (
    CustomerAccountCreate,
    CustomerAddressCreate,
    CustomerAddressPage,
    CustomerAddressResponse,
    CustomerContactCreate,
    CustomerContactPage,
    CustomerContactResponse,
    CustomerCreate,
    CustomerInvoicePage,
    CustomerInvoicePortalResponse,
    CustomerOrderPage,
    CustomerPage,
    CustomerPaymentPage,
    CustomerPaymentResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.schemas.invoices import InvoiceResponse
from app.schemas.orders import OrderResponse
from app.services.audit import log_activity
from app.services.customers import (
    create_customer,
    create_customer_address,
    create_customer_contact,
    customer_invoices,
    customer_orders,
    customer_payment_views,
    customer_summary,
    deactivate_customer,
    delete_customer_address,
    delete_customer_contact,
    get_customer,
    list_customer_addresses,
    list_customer_contacts,
    list_customers,
    paginate_customer_addresses,
    paginate_customer_contacts,
    paginate_customer_invoices,
    paginate_customer_orders,
    paginate_customer_payments,
    paginate_customers,
    update_customer,
    update_customer_address,
    update_customer_contact,
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse)
def post_customer(
    payload: CustomerCreate,
    membership=Depends(require_role(["admin", "manager", "staff"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            cust = create_customer(
                db,
                organization_id=org_id,
                name=payload.name,
                customer_code=payload.customer_code,
                company_name=payload.company_name,
                email=payload.email,
                phone=payload.phone,
                address=payload.address,
                billing_address=payload.billing_address,
                shipping_address=payload.shipping_address,
                status=payload.status,
                notes=payload.notes,
                credit_limit=payload.credit_limit,
                discount_percent=payload.discount_percent,
            )
            log_activity(db, organization_id=org_id, user=membership.user, action="CUSTOMER_CREATED", entity_type="CUSTOMER", entity_id=cust.id, details=f"Created customer {cust.name}")
    except ValueError as exc:
        raise HTTPException(status_code=409 if "exists" in str(exc) else 400, detail=str(exc)) from exc
    return cust


@router.get("", response_model=list[CustomerResponse] | CustomerPage)
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    status_filter: str | None = None,
    paginated: bool = False,
    membership=Depends(require_role(["admin", "manager", "staff"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    if paginated:
        return paginate_customers(db, org_id, page=page, page_size=page_size, q=q, phone=phone, email=email, status=status_filter)
    return list_customers(db, org_id, page=page, page_size=page_size, q=q, phone=phone, email=email, status=status_filter)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer_detail(
    customer_id: UUID,
    membership=Depends(require_role(["admin", "manager", "staff"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    cust = get_customer(db, org_id, customer_id)
    if cust is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return cust


@router.patch("/{customer_id}", response_model=CustomerResponse)
def patch_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    membership=Depends(require_role(["admin", "manager", "staff"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            cust = update_customer(
                db,
                organization_id=org_id,
                customer_id=customer_id,
                **payload.model_dump(exclude_unset=True),
            )
            log_activity(db, organization_id=org_id, user=membership.user, action="CUSTOMER_UPDATED", entity_type="CUSTOMER", entity_id=cust.id, details=f"Updated customer {cust.name}")
    except ValueError as exc:
        code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_409_CONFLICT if "exists" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return cust


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: UUID,
    membership=Depends(require_role(["admin", "manager", "staff"])),  # noqa: B008
    db: Session = Depends(get_db),
) -> Any:
    org_id = membership.organization_id
    try:
        with db.begin_nested():
            customer = deactivate_customer(db, organization_id=org_id, customer_id=customer_id)
            log_activity(db, organization_id=org_id, user=membership.user, action="CUSTOMER_DEACTIVATED", entity_type="CUSTOMER", entity_id=customer.id, details=f"Deactivated customer {customer.name}")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"success": True}


def _customer_or_404(db: Session, organization_id: UUID, customer_id: UUID) -> Customer:
    customer = get_customer(db, organization_id, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/orders", response_model=list[OrderResponse] | CustomerOrderPage)
def get_customer_orders(customer_id: UUID, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), paginated: bool = False, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        if paginated:
            return paginate_customer_orders(db, membership.organization_id, customer_id, page, page_size)
        return customer_orders(db, membership.organization_id, customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{customer_id}/invoices", response_model=list[InvoiceResponse] | CustomerInvoicePage)
def get_customer_invoices(customer_id: UUID, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), paginated: bool = False, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        if paginated:
            return paginate_customer_invoices(db, membership.organization_id, customer_id, page, page_size)
        return customer_invoices(db, membership.organization_id, customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{customer_id}/payments", response_model=list[CustomerPaymentResponse] | CustomerPaymentPage)
def get_customer_payments(customer_id: UUID, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), paginated: bool = False, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        if paginated:
            return paginate_customer_payments(db, membership.organization_id, customer_id, page, page_size)
        return customer_payment_views(db, membership.organization_id, customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{customer_id}/summary")
def get_customer_summary(customer_id: UUID, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        return customer_summary(db, membership.organization_id, customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{customer_id}/contacts", response_model=list[CustomerContactResponse] | CustomerContactPage)
def get_customer_contacts(customer_id: UUID, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), paginated: bool = False, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        if paginated:
            return paginate_customer_contacts(db, membership.organization_id, customer_id, page, page_size)
        return list_customer_contacts(db, membership.organization_id, customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{customer_id}/contacts", response_model=CustomerContactResponse, status_code=201)
def post_customer_contact(customer_id: UUID, payload: CustomerContactCreate, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        contact = create_customer_contact(db, membership.organization_id, customer_id, payload.model_dump())
        db.commit()
        db.refresh(contact)
        return contact
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{customer_id}/contacts/{contact_id}", response_model=CustomerContactResponse)
def patch_customer_contact(customer_id: UUID, contact_id: UUID, payload: CustomerContactCreate, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        contact = update_customer_contact(db, membership.organization_id, customer_id, contact_id, payload.model_dump())
        db.commit()
        db.refresh(contact)
        return contact
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{customer_id}/contacts/{contact_id}")
def remove_customer_contact(customer_id: UUID, contact_id: UUID, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        delete_customer_contact(db, membership.organization_id, customer_id, contact_id)
        db.commit()
        return {"success": True}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{customer_id}/addresses", response_model=list[CustomerAddressResponse] | CustomerAddressPage)
def get_customer_addresses(customer_id: UUID, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), paginated: bool = False, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        if paginated:
            return paginate_customer_addresses(db, membership.organization_id, customer_id, page, page_size)
        return list_customer_addresses(db, membership.organization_id, customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{customer_id}/addresses", response_model=CustomerAddressResponse, status_code=201)
def post_customer_address(customer_id: UUID, payload: CustomerAddressCreate, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        address = create_customer_address(db, membership.organization_id, customer_id, payload.model_dump())
        db.commit()
        db.refresh(address)
        return address
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{customer_id}/addresses/{address_id}", response_model=CustomerAddressResponse)
def patch_customer_address(customer_id: UUID, address_id: UUID, payload: CustomerAddressCreate, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        address = update_customer_address(db, membership.organization_id, customer_id, address_id, payload.model_dump())
        db.commit()
        db.refresh(address)
        return address
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{customer_id}/addresses/{address_id}")
def remove_customer_address(customer_id: UUID, address_id: UUID, membership=Depends(require_role(["admin", "manager", "staff"])), db: Session = Depends(get_db)) -> Any:
    try:
        delete_customer_address(db, membership.organization_id, customer_id, address_id)
        db.commit()
        return {"success": True}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{customer_id}/account", response_model=UserPublic)
def create_customer_account(customer_id: UUID, payload: CustomerAccountCreate, membership=Depends(require_role(["admin", "manager"])), db: Session = Depends(get_db)) -> Any:
    customer = _customer_or_404(db, membership.organization_id, customer_id)
    email = payload.email.strip().lower()
    password = payload.password
    if not email:
        raise HTTPException(status_code=422, detail="A valid email and password of at least 8 characters are required")
    if db.query(User).filter(User.email == email).first() is not None:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    role = db.query(Role).filter(Role.organization_id == membership.organization_id, Role.name == "customer").first()
    if role is None:
        role = Role(organization_id=membership.organization_id, name="customer", description="Customer portal user", is_system_role=True)
        db.add(role)
        db.flush()
    user = User(email=email, full_name=customer.name, password_hash=hash_password(password), is_active=True)
    db.add(user)
    db.flush()
    db.add(OrganizationMembership(organization_id=membership.organization_id, user_id=user.id, role_id=role.id, is_active=True))
    customer.user_id = user.id
    db.commit()
    db.refresh(user)
    return user


def _portal_customer(db: Session, user: User) -> Customer:
    customer = db.query(Customer).join(OrganizationMembership, OrganizationMembership.organization_id == Customer.organization_id).join(Role, Role.id == OrganizationMembership.role_id).filter(Customer.user_id == user.id, Customer.is_active.is_(True), Customer.status.notin_(["INACTIVE", "BLOCKED"]), OrganizationMembership.user_id == user.id, OrganizationMembership.is_active.is_(True), Role.name == "customer").first()
    if customer is None:
        raise HTTPException(status_code=403, detail="Active customer account required")
    return customer


@router.get("/portal/orders/{order_id}", response_model=OrderResponse)
def get_portal_order(order_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
    customer = _portal_customer(db, user)
    order = db.query(Order).options(selectinload(Order.items).selectinload(OrderItem.product)).filter(Order.id == order_id, Order.organization_id == customer.organization_id, Order.customer_id == customer.id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/portal/invoices/{invoice_id}", response_model=CustomerInvoicePortalResponse)
def get_portal_invoice(invoice_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
    customer = _portal_customer(db, user)
    invoice = db.query(Invoice).options(selectinload(Invoice.line_items)).filter(Invoice.id == invoice_id, Invoice.organization_id == customer.organization_id, Invoice.customer_id == customer.id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"invoice": InvoiceResponse.model_validate(invoice), "payments": customer_payment_views(db, customer.organization_id, customer.id)}


@router.get("/portal/me")
def get_customer_portal(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
    customer = _portal_customer(db, user)
    return jsonable_encoder({"customer": CustomerResponse.model_validate(customer), "summary": customer_summary(db, customer.organization_id, customer.id), "contacts": list_customer_contacts(db, customer.organization_id, customer.id), "addresses": list_customer_addresses(db, customer.organization_id, customer.id), "orders": customer_orders(db, customer.organization_id, customer.id), "invoices": customer_invoices(db, customer.organization_id, customer.id), "payments": customer_payment_views(db, customer.organization_id, customer.id)})
