# API Documentation

Base URL for local development: `http://127.0.0.1:8000`

## Authentication

Use `Authorization: Bearer <token>` for protected routes.

### Login

`POST /api/v1/auth/login`

```json
{
  "email": "admin@finance.local",
  "password": "Admin123!"
}
```

### Logout

`POST /api/v1/auth/logout`

### Current User

`GET /api/v1/me`

## Default Users

- `admin@finance.local` / `Admin123!`
- `analyst@finance.local` / `Analyst123!`
- `viewer@finance.local` / `Viewer123!`

## Users

Admin-only endpoints.

### Create User

`POST /api/v1/users`

```json
{
  "full_name": "QA User",
  "email": "qa@finance.local",
  "password": "QaUser123!",
  "role": "viewer",
  "status": "active"
}
```

### List Users

`GET /api/v1/users`

### Get User

`GET /api/v1/users/{user_id}`

### Update User

`PATCH /api/v1/users/{user_id}`

Supported fields:

- `full_name`
- `email`
- `password`
- `role`
- `status`

### Delete User

`DELETE /api/v1/users/{user_id}`

Soft deletes the user and revokes their active tokens.

## Financial Records

### Create Record

`POST /api/v1/records`

```json
{
  "amount": "2500.00",
  "type": "income",
  "category": "Consulting",
  "date": "2026-03-30",
  "notes": "March invoice"
}
```

### List Records

`GET /api/v1/records`

Query parameters:

- `type`
- `category`
- `start_date`
- `end_date`
- `limit`
- `offset`

### Get Record

`GET /api/v1/records/{record_id}`

### Update Record

`PATCH /api/v1/records/{record_id}`

Supported fields:

- `amount`
- `type`
- `category`
- `date`
- `notes`

### Delete Record

`DELETE /api/v1/records/{record_id}`

Soft deletes the record.

## Dashboard

### Summary

`GET /api/v1/dashboard/summary`

Returns total income, total expenses, and net balance.

### Category Breakdown

`GET /api/v1/dashboard/category-breakdown`

Returns grouped totals by category and type.

### Trends

`GET /api/v1/dashboard/trends?period=month`

Supported periods:

- `month`
- `week`

### Recent Activity

`GET /api/v1/dashboard/recent-activity`

Optional query parameter:

- `limit`

## Error Shape

All errors use this JSON format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation failed.",
    "details": {
      "field": "Problem description"
    }
  }
}
```

