# Finance Data Processing and Access Control Backend

A backend assignment solution for a finance dashboard system. It supports user management, token-based access control, financial record CRUD, and summary APIs for dashboard-style analytics.

## Stack

- Python 3.12
- Python standard library WSGI server
- SQLite for persistence

This project intentionally uses no third-party packages so the reviewer can run it with a single Python command.

## Features Implemented

- Role-based access control with `viewer`, `analyst`, and `admin`
- Token-based authentication with login and logout endpoints
- User management for admins
- Financial record create, read, update, delete, and filtering
- Dashboard summary endpoints:
  - total income
  - total expenses
  - net balance
  - category-wise totals
  - monthly or weekly trends
  - recent activity
- Input validation and consistent JSON error handling
- SQLite-backed persistence with seeded demo users
- Integration-style tests with `unittest`
- Human-readable API docs at `/docs`
- OpenAPI-style JSON document at `/openapi.json`

## Roles and Permissions

- `viewer`: can access dashboard summary endpoints only
- `analyst`: can read records and access dashboard summary endpoints
- `admin`: full user management, full record management, and dashboard access

## Project Structure

```text
.
|-- main.py
|-- src/finance_api
|   |-- app.py
|   |-- auth.py
|   |-- config.py
|   |-- database.py
|   |-- services/
|   |-- validation.py
|-- tests/
|-- docs/
```

## Run Locally

1. Start the server:

```bash
python main.py
```

2. Open the docs:

```text
http://127.0.0.1:8000/docs
```

3. Default seeded accounts:

- `admin@finance.local` / `Admin123!`
- `analyst@finance.local` / `Analyst123!`
- `viewer@finance.local` / `Viewer123!`

The SQLite database is created automatically at `data/finance.db`.

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## API Overview

### Auth

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/me`

### Users

- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`

### Records

- `GET /api/v1/records`
- `POST /api/v1/records`
- `GET /api/v1/records/{record_id}`
- `PATCH /api/v1/records/{record_id}`
- `DELETE /api/v1/records/{record_id}`

Supported record filters:

- `type`
- `category`
- `start_date`
- `end_date`
- `limit`
- `offset`

### Dashboard

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/category-breakdown`
- `GET /api/v1/dashboard/trends?period=month|week`
- `GET /api/v1/dashboard/recent-activity`

Dashboard endpoints also support `type`, `category`, `start_date`, and `end_date` filters where relevant.

## Example Requests

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@finance.local","password":"Admin123!"}'
```

### Create a Financial Record

```bash
curl -X POST http://127.0.0.1:8000/api/v1/records \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"amount":"2500.00","type":"income","category":"Consulting","date":"2026-03-30","notes":"March invoice"}'
```

### Fetch Dashboard Summary

```bash
curl http://127.0.0.1:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer <TOKEN>"
```

## Technical Decisions and Trade-offs

### Why standard library plus SQLite?

- It keeps local setup friction extremely low for evaluation.
- It demonstrates backend design clearly without hiding logic behind framework magic.
- SQLite is enough for this scope and still shows real persistence, querying, and aggregation.

### Why bearer tokens instead of a mock header?

- Tokens make the API feel closer to a real backend while remaining lightweight.
- They let the access-control flow be demonstrated cleanly across endpoints.

### Why store money as integer cents?

- It avoids floating-point precision issues in finance calculations.
- Responses include both a human-readable string amount and an integer cent value.

### Why soft delete users and records?

- It prevents accidental hard deletion during review.
- It keeps analytics safer by making delete behavior explicit and reversible in principle.

### Trade-offs

- The HTTP layer is custom and intentionally minimal, so it does not include production conveniences like middleware stacks, migrations, or automatic OpenAPI generation.
- Authentication is simplified for an assessment setting and does not include refresh tokens, password reset, or expiration policies.
- The docs page is static rather than interactive Swagger UI because the project avoids third-party dependencies.

## Assumptions

- Viewers only need dashboard summaries, not raw record access.
- Analysts can inspect records and summary data but cannot mutate records.
- Admins are the only role allowed to manage users and write records.
- User deletion is implemented as a soft delete plus token revocation.


