# System Design

NEXUS is designed as a modular monolith with a Next.js frontend and FastAPI backend. The backend owns business rules, authorization, inventory consistency, audit logging, invoice generation, analytics, and all database access.

## Current Phase

Phase 9 adds controlled Business Intelligence over existing tenant-scoped business tables. No external AI provider is required: natural-language questions are mapped by a deterministic server-side parser to an allowlisted analytics operation.

## Planned Runtime Architecture

```text
Next.js frontend
  -> FastAPI REST API (/api/v1)
  -> Supabase PostgreSQL
  -> Redis for caching, rate limiting, and background coordination
```

## Design Principles

- Backend authorization is authoritative.
- Financial totals are recalculated server-side.
- Inventory changes are auditable through movement history.
- Environment variables are used for all secrets.
- AI access is mediated by approved backend tools and services.
- Analytics access is limited to predefined server-side operations for administrator and manager roles.
- Analytics queries never accept raw SQL, arbitrary ORM expressions, code, filesystem access, or unrestricted tool calls.
- Analytics results are scoped from the authenticated organization membership and query access is audit logged.
- Procurement uses a controlled purchase-order state machine: `DRAFT -> SUBMITTED -> APPROVED -> PARTIALLY_RECEIVED -> RECEIVED`, with cancellation restricted to eligible pre-receipt states.
- Purchase-order receiving reuses the inventory stock-in service and immutable inventory transactions so stock and receipt state update atomically.
- Warehouses are separate branch-linked locations, preserving branch-level inventory APIs for backward compatibility while adding warehouse-specific stock records.
- Warehouse inventory tracks physical and reserved quantities; available quantity is derived as physical quantity minus reserved quantity and cannot become negative.
- Transfer dispatch and receipt use locked warehouse inventory rows and immutable movement transactions in one database transaction.
- Internal membership APIs reject customer-role accounts; customer accounts are limited to server-authorized portal resources owned by their linked customer.
- Management mutations for catalog, inventory, invoices, payments, transfers, and procurement require explicit admin or manager roles.
- Payment and legacy order mutations lock tenant-scoped aggregates before changing financial or inventory state.
- Customer history APIs support backward-compatible array responses and opt-in metadata pagination for new clients.

## Phase 14 lifecycle rules

The service transition maps are authoritative and are evaluated while holding the aggregate row lock. Terminal states are immutable:

- Legacy orders: `DRAFT -> CONFIRMED -> COMPLETED`; `CONFIRMED -> CANCELLED`.
- Sales orders: `DRAFT -> SUBMITTED|CONFIRMED|CANCELLED`, `SUBMITTED -> APPROVED|CANCELLED`, `APPROVED|CONFIRMED -> RESERVED`, `RESERVED -> PARTIALLY_FULFILLED|FULFILLED`, `PARTIALLY_FULFILLED -> FULFILLED|CANCELLED`, `FULFILLED -> INVOICED|CANCELLED`, `INVOICED -> PAID|CANCELLED`, `PAID -> COMPLETED`; `COMPLETED` and `CANCELLED` are terminal.
- Purchase orders: `DRAFT -> SUBMITTED|CANCELLED`, `SUBMITTED -> APPROVED|CANCELLED`, `APPROVED -> PARTIALLY_RECEIVED|RECEIVED|CANCELLED`, `PARTIALLY_RECEIVED -> RECEIVED`; `RECEIVED` and `CANCELLED` are terminal.
- Invoices: `DRAFT -> ISSUED|VOID`, `ISSUED -> PARTIAL|PAID|VOID`, `PARTIAL -> PAID|VOID`; `PAID` and `VOID` are terminal.
- Transfers: `REQUESTED -> APPROVED|CANCELLED`, `APPROVED -> IN_TRANSIT|CANCELLED`, `IN_TRANSIT -> COMPLETED`; `COMPLETED` and `CANCELLED` are terminal.
- Reservations: `ACTIVE -> RELEASED|CONSUMED`; released or consumed reservations cannot be reused.

Purchase receipts use an organization-scoped unique idempotency key and a request fingerprint. The receipt row is persisted before inventory movement inside the same transaction; PostgreSQL row locks and the database uniqueness constraint serialize duplicate operations. SQLite test runs cannot prove cross-connection row-lock behavior.

Customer contacts and addresses now use tenant-aware composite foreign keys to prevent a child in one organization from referencing a customer in another. The migration aborts with an explicit diagnostic if legacy cross-tenant rows are detected.

