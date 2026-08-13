# API Overview

The backend API is versioned under `/api/v1`.

## Implemented in Phase 0 (Foundation)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Confirms the API process is running |

## Implemented in Phase 3 (Authentication + RBAC)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | Register new user + organization |
| POST | `/api/v1/auth/login` | Authenticate user, issue JWT |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Retrieve authenticated user + org |

## Implemented in Phase 4 (Inventory & Product Management)

### Products

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/products` | Create product |
| GET | `/api/v1/products` | List products (paginated, searchable) |
| GET | `/api/v1/products/{product_id}` | Get product details |
| PATCH | `/api/v1/products/{product_id}` | Update product |
| DELETE | `/api/v1/products/{product_id}` | Soft-delete (is_active = false) |

### Categories

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/categories` | Create category |
| GET | `/api/v1/categories` | List categories |
| GET | `/api/v1/categories/{category_id}` | Get category details |
| PATCH | `/api/v1/categories/{category_id}` | Update category |
| DELETE | `/api/v1/categories/{category_id}` | Soft-delete |

### Branches

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/branches` | Create branch |
| GET | `/api/v1/branches` | List branches |
| GET | `/api/v1/branches/{branch_id}` | Get branch details |
| PATCH | `/api/v1/branches/{branch_id}` | Update branch |
| DELETE | `/api/v1/branches/{branch_id}` | Soft-delete |

### Inventory

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/inventory/stock-in` | Add stock (atomic) |
| POST | `/api/v1/inventory/stock-out` | Remove stock (validates availability, atomic) |
| POST | `/api/v1/inventory/adjust` | Manual adjustment (IN or OUT) |
| GET | `/api/v1/inventory` | List inventory items (supports low-stock filter, pagination) |
| GET | `/api/v1/inventory/{inventory_id}` | Get inventory details |
| GET | `/api/v1/inventory/{inventory_id}/transactions` | Get movement history (paginated, filterable by type) |

## Planned API Areas

- Suppliers (CRUD)
- Purchase orders, sales orders
- Customers, orders, payments, and invoices
- Dashboard analytics
- Audit logs and notifications
- Controlled AI analytics tools

