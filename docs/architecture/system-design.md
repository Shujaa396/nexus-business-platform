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

