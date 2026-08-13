# Database Design

The production database is a remote Supabase-hosted PostgreSQL instance and is accessed through the `DATABASE_URL` environment variable.

This repository has completed Phases 0-3 (project foundation, database foundation, multi-tenant schema, authentication) and is implementing Phase 4: Inventory & Product Management.

## Production Database Strategy

- Database engine: PostgreSQL
- Hosting: Supabase
- Access pattern: environment-managed `DATABASE_URL`
- Local development: no local PostgreSQL requirement for this phase
- Migration tool: Alembic with SQLAlchemy metadata discovery

## Completed Tables (Phase 2-4)

### Identity & Multi-Tenancy

- organizations: root tenant record
- users: user accounts with password_hash
- roles: organization-scoped roles
- organization_memberships: tracks user + org + role binding

### Business Structure (Phase 2)

- branches: physical/logical business locations
- categories: product category hierarchy

### Commercial Operations (Phase 2-4)

- products: SKU, pricing, tax, category
- customers: customer master data
- suppliers: supplier master data

### Inventory Management (Phase 4)

- inventory_items: current stock state (quantity, reorder_level) per branch/product
- inventory_transactions: immutable audit trail of stock movements
	- transaction types: STOCK_IN, STOCK_OUT, ADJUSTMENT_IN, ADJUSTMENT_OUT
	- supports future reference_type/reference_id for POs, SOs, etc.

## Inventory Schema Details

### InventoryItem

Represents the current state of a product's stock at a branch.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | primary key |
| organization_id | UUID | tenant |
| branch_id | UUID | physical/logical location |
| product_id | UUID | what product |
| quantity | Numeric(18,4) | >= 0 always |
| reorder_level | Numeric(18,4) | low-stock threshold |
| created_at, updated_at | TIMESTAMP(tz) | |

**Unique**: (organization_id, branch_id, product_id)

### InventoryTransaction

Immutable audit log of every stock movement.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | primary key |
| organization_id | UUID | tenant |
| branch_id | UUID | location |
| product_id | UUID | product |
| inventory_item_id | UUID | linked to state (FK) |
| transaction_type | String | STOCK_IN, STOCK_OUT, ADJUSTMENT_IN, ADJUSTMENT_OUT |
| quantity | Numeric(18,4) | amount moved |
| reference_type, reference_id | optional | future: PO, SO, etc. |
| notes | Text | reason |
| created_by | UUID | user (FK to users) |
| created_at | TIMESTAMP(tz) | immutable |

## Stock Movement Design

### STOCK_IN

- Increases inventory.quantity
- Creates STOCK_IN transaction
- Atomic: both changes or neither
- Used for: purchases, returns, initial stock, corrections up

### STOCK_OUT

- Decreases inventory.quantity
- Validates sufficient stock (rejects if quantity < requested)
- Creates STOCK_OUT transaction
- Atomic: both changes or neither
- Used for: sales, damage removal, corrections down
- Never allows negative stock

### ADJUSTMENT_IN / ADJUSTMENT_OUT

- Manual correction after physical count
- Used when audit detects discrepancy
- Follows STOCK_IN or STOCK_OUT logic respectively

## Concurrency & Atomicity

- Stock modification uses PostgreSQL SELECT ... FOR UPDATE (row locking)
- Prevents race conditions in concurrent stock-out operations
- Quantity change + transaction creation always atomic (single transaction)
- If any operation fails → ROLLBACK (both changes undone)

## Tenant Isolation

Every inventory query scoped by organization_id:
- User derives organization from authenticated membership
- All operations validate: branch ∈ org, product ∈ org, user ∈ org
- Never trusts organization_id from client request

## Planned Future Domains

### Identity and Access

- users
- roles
- permissions
- refresh_tokens

### Business Structure

- branches
- departments
- teams

### Commercial Operations

- customers
- products
- inventory
- inventory_movements
- orders
- order_items
- payments
- invoices
- expenses

### Operational and Audit Layers

- notifications
- audit_logs
- analytics_events

## Design Notes

- All future tables will be modeled with SQLAlchemy declarative base classes.
- Alembic will detect models via `Base.metadata` for future migration generation.
- No business tables are created in this phase.
- Authentication, products, inventory, and orders are intentionally deferred to later phases.

