from __future__ import annotations

import sqlite3
from typing import Any

from ..database import Database
from ..errors import ApiError
from ..utils import cents_to_amount_string, utc_now
from ..validation import (
    ensure_json_object,
    optional_string,
    parse_amount_to_cents,
    parse_identifier,
    parse_positive_int,
    validate_iso_date,
    validate_record_type,
)


def _serialize_record(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "amount": cents_to_amount_string(row["amount_cents"]),
        "amount_cents": row["amount_cents"],
        "type": row["entry_type"],
        "category": row["category"],
        "date": row["entry_date"],
        "notes": row["notes"],
        "created_by_user_id": row["created_by_user_id"],
        "updated_by_user_id": row["updated_by_user_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_record_row(connection: sqlite3.Connection, record_id: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM financial_records WHERE id = ? AND deleted_at IS NULL",
        (record_id,),
    ).fetchone()
    if row is None:
        raise ApiError(404, "Record not found.", code="not_found")
    return row


def _extract_filters(query: dict[str, list[str]], *, include_pagination: bool = True) -> dict[str, object]:
    filters: dict[str, object] = {}

    record_type = query.get("type", [None])[-1]
    if record_type:
        filters["type"] = validate_record_type(record_type)

    category = query.get("category", [None])[-1]
    if category:
        cleaned_category = optional_string(category, "category", max_length=80)
        if cleaned_category:
            filters["category"] = cleaned_category

    start_date = query.get("start_date", [None])[-1]
    end_date = query.get("end_date", [None])[-1]
    if start_date:
        filters["start_date"] = validate_iso_date(start_date, "start_date")
    if end_date:
        filters["end_date"] = validate_iso_date(end_date, "end_date")

    if "start_date" in filters and "end_date" in filters and filters["start_date"] > filters["end_date"]:
        raise ApiError(
            422,
            "Validation failed.",
            code="validation_error",
            details={"date_range": "start_date must be less than or equal to end_date."},
        )

    if include_pagination:
        filters["limit"] = parse_positive_int(
            query.get("limit", [None])[-1],
            "limit",
            default=20,
            minimum=1,
            maximum=100,
        )
        filters["offset"] = parse_positive_int(
            query.get("offset", [None])[-1],
            "offset",
            default=0,
            minimum=0,
        )

    return filters


def _build_where_clause(filters: dict[str, object]) -> tuple[str, list[object]]:
    clauses = ["deleted_at IS NULL"]
    params: list[object] = []

    if filters.get("type"):
        clauses.append("entry_type = ?")
        params.append(filters["type"])
    if filters.get("category"):
        clauses.append("LOWER(category) = LOWER(?)")
        params.append(filters["category"])
    if filters.get("start_date"):
        clauses.append("entry_date >= ?")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        clauses.append("entry_date <= ?")
        params.append(filters["end_date"])

    return " AND ".join(clauses), params


def list_records(database: Database, query: dict[str, list[str]]) -> dict[str, object]:
    filters = _extract_filters(query, include_pagination=True)
    where_clause, where_params = _build_where_clause(filters)

    with database.connect() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) AS count FROM financial_records WHERE {where_clause}",
            where_params,
        ).fetchone()["count"]
        rows = connection.execute(
            f"""
            SELECT *
            FROM financial_records
            WHERE {where_clause}
            ORDER BY entry_date DESC, created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            [*where_params, filters["limit"], filters["offset"]],
        ).fetchall()

    return {
        "data": [_serialize_record(row) for row in rows],
        "meta": {
            "total": total,
            "limit": filters["limit"],
            "offset": filters["offset"],
            "filters": {
                key: value
                for key, value in filters.items()
                if key not in {"limit", "offset"} and value is not None
            },
        },
    }


def get_record(database: Database, record_id_value: str) -> dict[str, object]:
    record_id = parse_identifier(record_id_value, "record_id")
    with database.connect() as connection:
        row = _get_record_row(connection, record_id)
    return _serialize_record(row)


def _validate_record_payload(payload: object, *, partial: bool = False) -> dict[str, object]:
    body = ensure_json_object(payload)
    cleaned: dict[str, object] = {}

    if not partial or "amount" in body:
        cleaned["amount_cents"] = parse_amount_to_cents(body.get("amount"))
    if not partial or "type" in body:
        cleaned["entry_type"] = validate_record_type(body.get("type"))
    if not partial or "category" in body:
        category = optional_string(body.get("category"), "category", max_length=80)
        if not category:
            raise ApiError(
                422,
                "Validation failed.",
                code="validation_error",
                details={"category": "Must not be empty."},
            )
        cleaned["category"] = category
    if not partial or "date" in body:
        cleaned["entry_date"] = validate_iso_date(body.get("date"))
    if "notes" in body or not partial:
        cleaned["notes"] = optional_string(body.get("notes"), "notes", max_length=500)

    return cleaned


def create_record(database: Database, payload: object, current_user: dict[str, object]) -> dict[str, object]:
    cleaned = _validate_record_payload(payload, partial=False)
    now = utc_now()

    with database.connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO financial_records (
                amount_cents,
                entry_type,
                category,
                entry_date,
                notes,
                created_by_user_id,
                updated_by_user_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cleaned["amount_cents"],
                cleaned["entry_type"],
                cleaned["category"],
                cleaned["entry_date"],
                cleaned["notes"],
                current_user["id"],
                current_user["id"],
                now,
                now,
            ),
        )
        connection.commit()
        row = _get_record_row(connection, cursor.lastrowid)
    return _serialize_record(row)


def update_record(
    database: Database,
    record_id_value: str,
    payload: object,
    current_user: dict[str, object],
) -> dict[str, object]:
    record_id = parse_identifier(record_id_value, "record_id")
    body = ensure_json_object(payload)
    if not body:
        raise ApiError(
            422,
            "Validation failed.",
            code="validation_error",
            details={"body": "At least one field must be provided."},
        )

    cleaned = _validate_record_payload(body, partial=True)
    if not cleaned:
        raise ApiError(
            422,
            "Validation failed.",
            code="validation_error",
            details={"body": "No supported fields were provided."},
        )

    assignments = [f"{column} = ?" for column in cleaned]
    params = list(cleaned.values())
    params.extend([current_user["id"], utc_now(), record_id])

    with database.connect() as connection:
        _get_record_row(connection, record_id)
        connection.execute(
            f"""
            UPDATE financial_records
            SET {", ".join(assignments)}, updated_by_user_id = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            params,
        )
        connection.commit()
        row = _get_record_row(connection, record_id)
    return _serialize_record(row)


def delete_record(database: Database, record_id_value: str, current_user: dict[str, object]) -> None:
    record_id = parse_identifier(record_id_value, "record_id")
    now = utc_now()
    with database.connect() as connection:
        _get_record_row(connection, record_id)
        connection.execute(
            """
            UPDATE financial_records
            SET deleted_at = ?, updated_at = ?, updated_by_user_id = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, current_user["id"], record_id),
        )
        connection.commit()


def filters_for_dashboard(query: dict[str, list[str]]) -> dict[str, object]:
    return _extract_filters(query, include_pagination=False)


def build_dashboard_where(filters: dict[str, object]) -> tuple[str, list[object]]:
    return _build_where_clause(filters)

