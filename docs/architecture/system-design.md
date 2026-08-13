# System Design

NEXUS is designed as a modular monolith with a Next.js frontend and FastAPI backend. The backend owns business rules, authorization, inventory consistency, audit logging, invoice generation, analytics, and all database access.

## Current Phase

Phase 0 establishes the monorepo, development tooling, documentation structure, and minimal health checks. No database tables, authentication flows, or production credentials are introduced in this phase.

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

