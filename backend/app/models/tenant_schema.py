from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list[Role]] = relationship("Role", back_populates="organization")
    branches: Mapped[list[Branch]] = relationship("Branch", back_populates="organization")
    categories: Mapped[list[Category]] = relationship("Category", back_populates="organization")
    products: Mapped[list[Product]] = relationship("Product", back_populates="organization")
    customers: Mapped[list[Customer]] = relationship("Customer", back_populates="organization")
    suppliers: Mapped[list[Supplier]] = relationship("Supplier", back_populates="organization")
    memberships: Mapped[list[OrganizationMembership]] = relationship(
        "OrganizationMembership",
        back_populates="organization",
    )


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    memberships: Mapped[list[OrganizationMembership]] = relationship(
        "OrganizationMembership",
        back_populates="user",
    )


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_roles_organization_name"),
        Index("ix_roles_organization_id", "organization_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="roles")
    memberships: Mapped[list[OrganizationMembership]] = relationship(
        "OrganizationMembership",
        back_populates="role",
    )


class OrganizationMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_membership_org_user"),
        Index("ix_org_membership_org_id", "organization_id"),
        Index("ix_org_membership_user_id", "user_id"),
        Index("ix_org_membership_role_id", "role_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="memberships")
    user: Mapped[User] = relationship("User", back_populates="memberships")
    role: Mapped[Role] = relationship("Role", back_populates="memberships")


class Branch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_branches_organization_code"),
        Index("ix_branches_organization_id", "organization_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="branches")


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_categories_organization_name"),
        Index("ix_categories_organization_id", "organization_id"),
        Index("ix_categories_parent_id", "parent_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    parent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="categories")
    parent: Mapped[Category] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
    )
    children: Mapped[list[Category]] = relationship("Category", back_populates="parent")
    products: Mapped[list[Product]] = relationship("Product", back_populates="category")


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_products_organization_sku"),
        Index("ix_products_organization_id", "organization_id"),
        Index("ix_products_sku", "sku"),
        Index("ix_products_category_id", "category_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
    )
    sku: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="products")
    category: Mapped[Category] = relationship("Category", back_populates="products")


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_organization_id", "organization_id"),
        Index("ix_customers_email", "email"),
        Index("ix_customers_phone", "phone"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="customers")


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        Index("ix_suppliers_organization_id", "organization_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="suppliers")


class InventoryItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_items"
    __table_args__ = (
        Index("ix_inventory_items_organization_id", "organization_id"),
        Index("ix_inventory_items_branch_id", "branch_id"),
        Index("ix_inventory_items_product_id", "product_id"),
        UniqueConstraint("organization_id", "branch_id", "product_id", name="uq_inventory_org_branch_product"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)

    organization: Mapped[Organization] = relationship("Organization")
    branch: Mapped[Branch] = relationship("Branch")
    product: Mapped[Product] = relationship("Product")
    transactions: Mapped[list["InventoryTransaction"]] = relationship(
        "InventoryTransaction", back_populates="inventory_item", cascade="all, delete-orphan"
    )


class InventoryTransaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        Index("ix_inventory_tx_organization_id", "organization_id"),
        Index("ix_inventory_tx_branch_id", "branch_id"),
        Index("ix_inventory_tx_product_id", "product_id"),
        Index("ix_inventory_tx_created_at", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    inventory_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(120), nullable=True)
    reference_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    inventory_item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="transactions")
    organization: Mapped[Organization] = relationship("Organization")
    branch: Mapped[Branch] = relationship("Branch")
    product: Mapped[Product] = relationship("Product")
    creator: Mapped[User] = relationship("User")


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_organization_id", "organization_id"),
        Index("ix_orders_branch_id", "branch_id"),
        Index("ix_orders_order_number", "order_number"),
        UniqueConstraint("organization_id", "order_number", name="uq_orders_org_order_number"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    order_number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNPAID")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    organization: Mapped[Organization] = relationship("Organization")
    branch: Mapped[Branch] = relationship("Branch")
    customer: Mapped[Customer] = relationship("Customer")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    history: Mapped[list["OrderStatusHistory"]] = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")


class OrderItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"),
    )

    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="items")
    product: Mapped[Product] = relationship("Product")


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_organization_id", "organization_id"),
        Index("ix_payments_order_id", "order_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    reference: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")

    order: Mapped[Order] = relationship("Order", back_populates="payments")


class OrderStatusHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "order_status_history"
    __table_args__ = (
        Index("ix_order_status_history_order_id", "order_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    old_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    order: Mapped[Order] = relationship("Order", back_populates="history")
