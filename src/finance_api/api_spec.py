from __future__ import annotations


def get_openapi_spec() -> dict[str, object]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Finance Data Processing and Access Control API",
            "version": "0.1.0",
            "description": (
                "SQLite-backed finance dashboard API with token authentication, "
                "role-based access control, record management, and dashboard summaries."
            ),
        },
        "servers": [{"url": "http://localhost:8000"}],
        "tags": [
            {"name": "Health"},
            {"name": "Auth"},
            {"name": "Users"},
            {"name": "Records"},
            {"name": "Dashboard"},
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "Token",
                }
            }
        },
        "paths": {
            "/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Health check",
                    "responses": {"200": {"description": "Service is healthy"}},
                }
            },
            "/docs": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Human-readable API documentation",
                    "responses": {"200": {"description": "HTML documentation page"}},
                }
            },
            "/api/v1/auth/login": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Log in and receive a bearer token",
                    "responses": {"200": {"description": "Authenticated successfully"}},
                }
            },
            "/api/v1/auth/logout": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Revoke the current bearer token",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Token revoked"}},
                }
            },
            "/api/v1/me": {
                "get": {
                    "tags": ["Auth"],
                    "summary": "Return the current authenticated user",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Current user"}},
                }
            },
            "/api/v1/users": {
                "get": {
                    "tags": ["Users"],
                    "summary": "List users",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "User list"}},
                },
                "post": {
                    "tags": ["Users"],
                    "summary": "Create a user",
                    "security": [{"bearerAuth": []}],
                    "responses": {"201": {"description": "User created"}},
                },
            },
            "/api/v1/users/{user_id}": {
                "get": {
                    "tags": ["Users"],
                    "summary": "Get a single user",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "User details"}},
                },
                "patch": {
                    "tags": ["Users"],
                    "summary": "Update a user",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "User updated"}},
                },
                "delete": {
                    "tags": ["Users"],
                    "summary": "Soft delete a user",
                    "security": [{"bearerAuth": []}],
                    "responses": {"204": {"description": "User deleted"}},
                },
            },
            "/api/v1/records": {
                "get": {
                    "tags": ["Records"],
                    "summary": "List financial records with filters",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Record list"}},
                },
                "post": {
                    "tags": ["Records"],
                    "summary": "Create a financial record",
                    "security": [{"bearerAuth": []}],
                    "responses": {"201": {"description": "Record created"}},
                },
            },
            "/api/v1/records/{record_id}": {
                "get": {
                    "tags": ["Records"],
                    "summary": "Get a single record",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Record details"}},
                },
                "patch": {
                    "tags": ["Records"],
                    "summary": "Update a record",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Record updated"}},
                },
                "delete": {
                    "tags": ["Records"],
                    "summary": "Soft delete a record",
                    "security": [{"bearerAuth": []}],
                    "responses": {"204": {"description": "Record deleted"}},
                },
            },
            "/api/v1/dashboard/summary": {
                "get": {
                    "tags": ["Dashboard"],
                    "summary": "Income, expense, and net totals",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Dashboard summary"}},
                }
            },
            "/api/v1/dashboard/category-breakdown": {
                "get": {
                    "tags": ["Dashboard"],
                    "summary": "Category-wise totals",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Category totals"}},
                }
            },
            "/api/v1/dashboard/trends": {
                "get": {
                    "tags": ["Dashboard"],
                    "summary": "Monthly or weekly trends",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Trend buckets"}},
                }
            },
            "/api/v1/dashboard/recent-activity": {
                "get": {
                    "tags": ["Dashboard"],
                    "summary": "Most recent records",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": {"description": "Recent activity"}},
                }
            },
        },
    }

