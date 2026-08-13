# API Overview

The backend API is versioned under `/api/v1`.

## Implemented in Phase 0 (Foundation)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Confirms the API process is running |

## Phase 6 Invoice Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/invoices/from-order` | Creates a draft invoice from a confirmed or completed order |
| GET | `/api/v1/invoices` | Lists invoices scoped to the authenticated organization |
| GET | `/api/v1/invoices/{invoice_id}` | Retrieves one tenant-scoped invoice with line items |
| POST | `/api/v1/invoices/{invoice_id}/issue` | Moves a draft invoice to issued |
| POST | `/api/v1/invoices/{invoice_id}/payments/sync` | Updates invoice payment status from completed order payments or an explicit paid amount |

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

## Phase 7 Dashboard & Reporting Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/dashboard/summary` | Retrieve overall organization business summary metrics |
| GET | `/api/v1/dashboard/sales` | Sales and revenue analytics (supports preset, custom dates, period_type) |
| GET | `/api/v1/dashboard/sales/daily` | Shortcut endpoint for daily sales analytics |
| GET | `/api/v1/dashboard/sales/weekly` | Shortcut endpoint for weekly sales analytics |
| GET | `/api/v1/dashboard/sales/monthly` | Shortcut endpoint for monthly sales analytics |
| GET | `/api/v1/dashboard/products` | Product analytics (top selling, highest revenue, low stock, inventory value) |
| GET | `/api/v1/dashboard/customers` | Customer analytics (totals, new signups, top spenders) |
| GET | `/api/v1/dashboard/branches` | Branch analytics (order count, revenue, inventory item count & valuation) |

## Planned API Areas

- Suppliers (CRUD)
- Controlled AI analytics tools
