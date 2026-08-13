# NEXUS

NEXUS is a multi-branch business management and analytics platform built as a production-style full-stack monorepo. The system is planned around a Next.js frontend, FastAPI backend, Supabase-hosted PostgreSQL database, Redis-backed infrastructure features, and controlled AI-assisted business analytics.

This repository is currently at **Phase 1: Database Foundation**. Business tables, authentication, inventory, POS, invoices, analytics, and AI workflows are intentionally not implemented yet.

## Tech Stack

- Frontend: Next.js, TypeScript, App Router, Tailwind CSS
- Backend: Python, FastAPI, Pydantic
- Production database: Supabase PostgreSQL via `DATABASE_URL`
- Planned infrastructure: Redis, Docker, GitHub Actions

## Folder Structure

```text
nexus-business-platform/
  frontend/
  backend/
  docs/
  .github/
  docker-compose.yml
  .env.example
  README.md
```

## Setup

Copy environment templates before running locally:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

The production deployment uses a remote Supabase PostgreSQL database. Do not create or connect to a local PostgreSQL instance for app logic in this phase. The application reads the connection string from the `DATABASE_URL` environment variable.

## Database Foundation

The backend now includes the SQLAlchemy and Alembic foundation for PostgreSQL access without creating business tables yet.

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate
python -m pip install -r requirements.txt
```

Set `DATABASE_URL` in `backend/.env` before enabling database connectivity checks. Example:

```bash
DATABASE_URL=postgresql+psycopg://postgres:your-password@db.<project-ref>.supabase.co:5432/postgres
```

Alembic is configured to read `DATABASE_URL` from the environment rather than hardcoding credentials.

Install frontend dependencies:

```bash
cd frontend
npm install
```

Install backend dependencies:

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate
python -m pip install -r requirements.txt
```

## Running Locally

Frontend:

```bash
cd frontend
npm run dev
```

Backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Database status check (when `DATABASE_URL` is set):

```python
from app.db.health import database_health_status

print(database_health_status())
```

Backend health check:

```bash
curl http://localhost:8000/api/v1/health
```

Docker Compose currently provides Redis for local development support:

```bash
docker compose up -d
```

## Checks

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Backend:

```bash
cd backend
ruff check .
pytest
```

To verify the Alembic configuration without connecting to the remote database, set `DATABASE_URL` in the environment and run:

```bash
cd backend
DATABASE_URL=postgresql+psycopg://postgres:password@db.example.supabase.co:5432/postgres alembic -c alembic.ini check
```

## API Documentation

When the backend is running, FastAPI exposes OpenAPI documentation at:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Security Notes

- Secrets must be supplied through environment variables.
- Production database credentials must never be committed.
- The production PostgreSQL database is expected to be remote Supabase, not a required local service.
- AI features will use approved backend services only and will not receive unrestricted SQL/database access.

