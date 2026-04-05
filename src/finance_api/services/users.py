from __future__ import annotations

import sqlite3

from ..auth import generate_token, hash_password, verify_password
from ..database import Database
from ..errors import ApiError
from ..utils import utc_now
from ..validation import (
    ensure_json_object,
    optional_string,
    parse_identifier,
    require_non_empty_string,
    validate_email,
    validate_password,
    validate_role,
    validate_status,
)


def _serialize_user(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "full_name": row["full_name"],
        "email": row["email"],
        "role": row["role"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_user_row(connection: sqlite3.Connection, user_id: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM users WHERE id = ? AND deleted_at IS NULL",
        (user_id,),
    ).fetchone()
    if row is None:
        raise ApiError(404, "User not found.", code="not_found")
    return row


def authenticate_login(database: Database, payload: object) -> dict[str, object]:
    body = ensure_json_object(payload)
    email = validate_email(body.get("email"))
    password = require_non_empty_string(body.get("password"), "password", max_length=128)

    with database.connect() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ? AND deleted_at IS NULL",
            (email,),
        ).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            raise ApiError(401, "Invalid email or password.", code="unauthorized")
        if row["status"] != "active":
            raise ApiError(403, "Inactive users cannot authenticate.", code="inactive_user")

        now = utc_now()
        token = generate_token()
        connection.execute(
            """
            INSERT INTO auth_tokens (user_id, token, created_at, last_used_at)
            VALUES (?, ?, ?, ?)
            """,
            (row["id"], token, now, now),
        )
        connection.commit()

        return {
            "access_token": token,
            "token_type": "Bearer",
            "user": _serialize_user(row),
        }


def authenticate_request(database: Database, token: str | None) -> dict[str, object]:
    if not token:
        raise ApiError(401, "Missing bearer token.", code="unauthorized")

    with database.connect() as connection:
        row = connection.execute(
            """
            SELECT
                users.*,
                auth_tokens.id AS token_id,
                auth_tokens.token AS active_token
            FROM auth_tokens
            JOIN users ON users.id = auth_tokens.user_id
            WHERE auth_tokens.token = ?
              AND auth_tokens.revoked_at IS NULL
              AND users.deleted_at IS NULL
            """,
            (token,),
        ).fetchone()
        if row is None:
            raise ApiError(401, "Invalid or revoked bearer token.", code="unauthorized")
        if row["status"] != "active":
            raise ApiError(403, "Inactive users cannot access the API.", code="inactive_user")

        connection.execute(
            "UPDATE auth_tokens SET last_used_at = ? WHERE id = ?",
            (utc_now(), row["token_id"]),
        )
        connection.commit()

        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
            "status": row["status"],
            "token": row["active_token"],
        }


def logout(database: Database, current_user: dict[str, object]) -> dict[str, str]:
    token = str(current_user["token"])
    with database.connect() as connection:
        connection.execute(
            "UPDATE auth_tokens SET revoked_at = ? WHERE token = ? AND revoked_at IS NULL",
            (utc_now(), token),
        )
        connection.commit()
    return {"message": "Token revoked successfully."}


def list_users(database: Database) -> list[dict[str, object]]:
    with database.connect() as connection:
        rows = connection.execute(
            """
            SELECT id, full_name, email, role, status, created_at, updated_at
            FROM users
            WHERE deleted_at IS NULL
            ORDER BY id ASC
            """
        ).fetchall()
    return [_serialize_user(row) for row in rows]


def get_user(database: Database, user_id_value: str) -> dict[str, object]:
    user_id = parse_identifier(user_id_value, "user_id")
    with database.connect() as connection:
        row = _get_user_row(connection, user_id)
    return _serialize_user(row)


def create_user(database: Database, payload: object) -> dict[str, object]:
    body = ensure_json_object(payload)
    full_name = optional_string(body.get("full_name"), "full_name", max_length=100)
    if not full_name:
        raise ApiError(
            422,
            "Validation failed.",
            code="validation_error",
            details={"full_name": "Must not be empty."},
        )
    email = validate_email(body.get("email"))
    password = validate_password(body.get("password"))
    role = validate_role(body.get("role"))
    status = validate_status(body.get("status", "active"))
    now = utc_now()

    with database.connect() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO users (full_name, email, password_hash, role, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (full_name, email, hash_password(password), role, status, now, now),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ApiError(
                409,
                "A user with that email already exists.",
                code="conflict",
                details={"email": email},
            ) from exc

        row = _get_user_row(connection, cursor.lastrowid)
        return _serialize_user(row)


def update_user(
    database: Database,
    user_id_value: str,
    payload: object,
    current_user: dict[str, object],
) -> dict[str, object]:
    user_id = parse_identifier(user_id_value, "user_id")
    body = ensure_json_object(payload)
    if not body:
        raise ApiError(
            422,
            "Validation failed.",
            code="validation_error",
            details={"body": "At least one field must be provided."},
        )

    updates: list[str] = []
    params: list[object] = []

    if "full_name" in body:
        full_name = optional_string(body.get("full_name"), "full_name", max_length=100)
        if not full_name:
            raise ApiError(
                422,
                "Validation failed.",
                code="validation_error",
                details={"full_name": "Must not be empty."},
            )
        updates.append("full_name = ?")
        params.append(full_name)

    if "email" in body:
        updates.append("email = ?")
        params.append(validate_email(body.get("email")))

    if "password" in body:
        updates.append("password_hash = ?")
        params.append(hash_password(validate_password(body.get("password"))))

    if "role" in body:
        new_role = validate_role(body.get("role"))
        if current_user["id"] == user_id and new_role != "admin":
            raise ApiError(409, "Admins cannot remove their own admin role.", code="conflict")
        updates.append("role = ?")
        params.append(new_role)

    if "status" in body:
        new_status = validate_status(body.get("status"))
        if current_user["id"] == user_id and new_status != "active":
            raise ApiError(409, "Admins cannot deactivate themselves.", code="conflict")
        updates.append("status = ?")
        params.append(new_status)

    if not updates:
        raise ApiError(
            422,
            "Validation failed.",
            code="validation_error",
            details={"body": "No supported fields were provided."},
        )

    params.extend([utc_now(), user_id])

    with database.connect() as connection:
        _get_user_row(connection, user_id)
        try:
            connection.execute(
                f"""
                UPDATE users
                SET {", ".join(updates)}, updated_at = ?
                WHERE id = ? AND deleted_at IS NULL
                """,
                params,
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            raise ApiError(
                409,
                "A user with that email already exists.",
                code="conflict",
            ) from exc
        row = _get_user_row(connection, user_id)
        return _serialize_user(row)


def delete_user(database: Database, user_id_value: str, current_user: dict[str, object]) -> None:
    user_id = parse_identifier(user_id_value, "user_id")
    if current_user["id"] == user_id:
        raise ApiError(409, "Admins cannot delete themselves.", code="conflict")

    now = utc_now()
    with database.connect() as connection:
        _get_user_row(connection, user_id)
        connection.execute(
            """
            UPDATE users
            SET status = 'inactive', deleted_at = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, user_id),
        )
        connection.execute(
            "UPDATE auth_tokens SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
            (now, user_id),
        )
        connection.commit()
