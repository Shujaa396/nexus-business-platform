from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
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
    purchase_orders: Mapped[list[PurchaseOrder]] = relationship("PurchaseOrder", back_populates="organization")
    warehouses: Mapped[list[Warehouse]] = relationship("Warehouse", back_populates="organization")
    invoices: Mapped[list[Invoice]] = relationship("Invoice", back_populates="organization")
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
    refresh_tokens: Mapped[list[RefreshToken]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_hash: Mapped[str] = mapped_column(String(128), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")


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
    supplier_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
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
    supplier: Mapped[Supplier] = relationship("Supplier")


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("organization_id", "customer_code", name="uq_customers_organization_code"),
        UniqueConstraint("organization_id", "id", name="uq_customers_organization_id_id"),
        Index("ix_customers_organization_id", "organization_id"),
        Index("ix_customers_email", "email"),
        Index("ix_customers_phone", "phone"),
        Index("ix_customers_status", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_code: Mapped[str] = mapped_column(String(80), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    billing_address: Mapped[str] = mapped_column(Text, nullable=True)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True
    )

    organization: Mapped[Organization] = relationship("Organization", back_populates="customers")
    user: Mapped[User] = relationship("User")
    contacts: Mapped[list[CustomerContact]] = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan", foreign_keys="CustomerContact.customer_id")
    addresses: Mapped[list[CustomerAddress]] = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan", foreign_keys="CustomerAddress.customer_id")


class CustomerContact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_contacts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "customer_id"],
            ["customers.organization_id", "customers.id"],
            name="fk_customer_contacts_org_customer",
            ondelete="CASCADE",
        ),
        Index("ix_customer_contacts_organization_id", "organization_id"),
        Index("ix_customer_contacts_customer_id", "customer_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    job_title: Mapped[str] = mapped_column(String(120), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="contacts", foreign_keys=[customer_id])


class CustomerAddress(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_addresses"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "customer_id"],
            ["customers.organization_id", "customers.id"],
            name="fk_customer_addresses_org_customer",
            ondelete="CASCADE",
        ),
        Index("ix_customer_addresses_organization_id", "organization_id"),
        Index("ix_customer_addresses_customer_id", "customer_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    address_type: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=True)
    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(120), nullable=True)
    state: Mapped[str] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(40), nullable=True)
    country: Mapped[str] = mapped_column(String(120), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    customer: Mapped[Customer] = relationship("Customer", back_populates="addresses", foreign_keys=[customer_id])


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
    purchase_orders: Mapped[list[PurchaseOrder]] = relationship("PurchaseOrder", back_populates="supplier")


class Warehouse(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_warehouses_organization_code"),
        Index("ix_warehouses_organization_id", "organization_id"),
        Index("ix_warehouses_branch_id", "branch_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = relationship("Organization", back_populates="warehouses")
    branch: Mapped[Branch] = relationship("Branch")
    inventory: Mapped[list[WarehouseInventory]] = relationship("WarehouseInventory", back_populates="warehouse")


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
    transactions: Mapped[list[InventoryTransaction]] = relationship(
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
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True
    )

    inventory_item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="transactions")
    organization: Mapped[Organization] = relationship("Organization")
    branch: Mapped[Branch] = relationship("Branch")
    product: Mapped[Product] = relationship("Product")
    creator: Mapped[User] = relationship("User")


class WarehouseInventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "warehouse_inventory"
    __table_args__ = (
        UniqueConstraint("organization_id", "warehouse_id", "product_id", name="uq_warehouse_inventory_org_wh_product"),
        CheckConstraint("quantity >= 0", name="ck_warehouse_inventory_quantity_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_warehouse_inventory_reserved_nonnegative"),
        CheckConstraint("reserved_quantity <= quantity", name="ck_warehouse_inventory_reserved_lte_quantity"),
        Index("ix_warehouse_inventory_organization_id", "organization_id"),
        Index("ix_warehouse_inventory_warehouse_id", "warehouse_id"),
        Index("ix_warehouse_inventory_product_id", "product_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    reorder_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)

    @property
    def available_quantity(self) -> Decimal:
        return (self.quantity or Decimal(0)) - (self.reserved_quantity or Decimal(0))

    warehouse: Mapped[Warehouse] = relationship("Warehouse", back_populates="inventory")
    product: Mapped[Product] = relationship("Product")


class InventoryTransfer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_transfers"
    __table_args__ = (
        Index("ix_inventory_transfers_organization_id", "organization_id"),
        Index("ix_inventory_transfers_status", "status"),
        CheckConstraint("status IN ('DRAFT', 'REQUESTED', 'APPROVED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED')", name="ck_inventory_transfers_status"),
    )

    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    source_warehouse_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    destination_warehouse_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REQUESTED")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    items: Mapped[list[InventoryTransferItem]] = relationship("InventoryTransferItem", back_populates="transfer", cascade="all, delete-orphan")
    source_warehouse: Mapped[Warehouse] = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    destination_warehouse: Mapped[Warehouse] = relationship("Warehouse", foreign_keys=[destination_warehouse_id])


class InventoryTransferItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_transfer_items"
    __table_args__ = (UniqueConstraint("transfer_id", "product_id", name="uq_inventory_transfer_product"),)

    transfer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("inventory_transfers.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    transfer: Mapped[InventoryTransfer] = relationship("InventoryTransfer", back_populates="items")
    product: Mapped[Product] = relationship("Product")


class InventoryReservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_reservations"
    __table_args__ = (Index("ix_inventory_reservations_organization_id", "organization_id"), Index("ix_inventory_reservations_status", "status"))

    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    warehouse_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    reference_type: Mapped[str] = mapped_column(String(80), nullable=True)
    reference_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class PurchaseOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "purchase_order_number", name="uq_purchase_orders_org_number"),
        CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'CANCELLED')",
            name="ck_purchase_orders_status",
        ),
        Index("ix_purchase_orders_organization_id", "organization_id"),
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
        Index("ix_purchase_orders_branch_id", "branch_id"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_order_date", "order_date"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    supplier_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True
    )
    purchase_order_number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_delivery_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    organization: Mapped[Organization] = relationship("Organization", back_populates="purchase_orders")
    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="purchase_orders")
    branch: Mapped[Branch] = relationship("Branch")
    warehouse: Mapped[Warehouse] = relationship("Warehouse")
    creator: Mapped[User] = relationship("User")
    items: Mapped[list[PurchaseOrderItem]] = relationship(
        "PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan"
    )
    receipts: Mapped[list[PurchaseReceipt]] = relationship(
        "PurchaseReceipt", back_populates="purchase_order", cascade="all, delete-orphan"
    )


class PurchaseReceipt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_receipts"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_purchase_receipts_org_key"),
        Index("ix_purchase_receipts_purchase_order_id", "purchase_order_id"),
        Index("ix_purchase_receipts_organization_id", "organization_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    purchase_order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    organization: Mapped[Organization] = relationship("Organization")
    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="receipts")
    creator: Mapped[User] = relationship("User")
    items: Mapped[list[PurchaseReceiptItem]] = relationship(
        "PurchaseReceiptItem", back_populates="receipt", cascade="all, delete-orphan"
    )


class PurchaseReceiptItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_receipt_items"
    __table_args__ = (UniqueConstraint("receipt_id", "purchase_order_item_id", name="uq_purchase_receipt_item"),)

    receipt_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("purchase_receipts.id", ondelete="CASCADE"), nullable=False)
    purchase_order_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("purchase_order_items.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    receipt: Mapped[PurchaseReceipt] = relationship("PurchaseReceipt", back_populates="items")
    purchase_order_item: Mapped[PurchaseOrderItem] = relationship("PurchaseOrderItem")


class PurchaseOrderItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        Index("ix_purchase_order_items_purchase_order_id", "purchase_order_id"),
        Index("ix_purchase_order_items_product_id", "product_id"),
        UniqueConstraint("purchase_order_id", "product_id", name="uq_purchase_order_items_order_product"),
    )

    purchase_order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="items")
    product: Mapped[Product] = relationship("Product")


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
    warehouse_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    order_number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNPAID")
    requested_fulfillment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    organization: Mapped[Organization] = relationship("Organization")
    branch: Mapped[Branch] = relationship("Branch")
    warehouse: Mapped[Warehouse] = relationship("Warehouse")
    customer: Mapped[Customer] = relationship("Customer")
    items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    history: Mapped[list[OrderStatusHistory]] = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")


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
    fulfilled_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)

    order: Mapped[Order] = relationship("Order", back_populates="items")
    product: Mapped[Product] = relationship("Product")

    @property
    def product_name(self) -> str | None:
        return self.product.name if self.product else None

    @property
    def product_sku(self) -> str | None:
        return self.product.sku if self.product else None


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


class Invoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_organization_id", "organization_id"),
        Index("ix_invoices_branch_id", "branch_id"),
        Index("ix_invoices_customer_id", "customer_id"),
        Index("ix_invoices_order_id", "order_id"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        UniqueConstraint("organization_id", "invoice_number", name="uq_invoices_org_invoice_number"),
        UniqueConstraint("organization_id", "order_id", name="uq_invoices_org_order"),
        CheckConstraint(
            "status IN ('DRAFT', 'ISSUED', 'PARTIAL', 'PAID', 'VOID')",
            name="ck_invoices_status",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    order_number: Mapped[str] = mapped_column(String(64), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    issued_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    issued_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    organization: Mapped[Organization] = relationship("Organization", back_populates="invoices")
    order: Mapped[Order] = relationship("Order")
    branch: Mapped[Branch] = relationship("Branch")
    customer: Mapped[Customer] = relationship("Customer")
    issuer: Mapped[User] = relationship("User")
    line_items: Mapped[list[InvoiceLineItem]] = relationship(
        "InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan"
    )


class InvoiceLineItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invoice_line_items"
    __table_args__ = (
        Index("ix_invoice_line_items_organization_id", "organization_id"),
        Index("ix_invoice_line_items_invoice_id", "invoice_id"),
        Index("ix_invoice_line_items_order_item_id", "order_item_id"),
        Index("ix_invoice_line_items_product_id", "product_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    order_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("order_items.id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    product_sku: Mapped[str] = mapped_column(String(120), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="line_items")
    order_item: Mapped[OrderItem] = relationship("OrderItem")
    organization: Mapped[Organization] = relationship("Organization")
    product: Mapped[Product] = relationship("Product")


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_organization_id", "organization_id"),
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_entity_type", "entity_type"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    user_email: Mapped[str] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(80), nullable=True)

    organization: Mapped[Organization] = relationship("Organization")
    user: Mapped[User] = relationship("User")



