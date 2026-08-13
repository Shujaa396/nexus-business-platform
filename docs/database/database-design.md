# Database Design

The production database is a remote Supabase-hosted PostgreSQL instance and is accessed through the `DATABASE_URL` environment variable.

This repository is currently in Phase 1: database foundation. The system does not create business tables yet. The focus is the SQLAlchemy base layer, Alembic migration configuration, environment-driven database settings, and the schema design plan for future migrations.

## Production Database Strategy

- Database engine: PostgreSQL
- Hosting: Supabase
- Access pattern: environment-managed `DATABASE_URL`
- Local development: no local PostgreSQL requirement for this phase
- Migration tool: Alembic with SQLAlchemy metadata discovery

## Planned Core Domains

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

