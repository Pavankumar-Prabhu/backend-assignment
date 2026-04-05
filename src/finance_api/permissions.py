from __future__ import annotations

from .errors import ApiError


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "viewer": {"dashboard:read"},
    "analyst": {"dashboard:read", "records:read"},
    "admin": {
        "dashboard:read",
        "records:read",
        "records:write",
        "users:read",
        "users:write",
    },
}


def ensure_permission(user: dict[str, object], permission: str) -> None:
    role = str(user.get("role", ""))
    allowed_permissions = ROLE_PERMISSIONS.get(role, set())
    if permission not in allowed_permissions:
        raise ApiError(
            403,
            "You do not have permission to perform this action.",
            code="forbidden",
            details={"required_permission": permission, "role": role},
        )

