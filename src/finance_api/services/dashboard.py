from __future__ import annotations

from ..database import Database
from ..errors import ApiError
from ..utils import money_payload
from ..validation import parse_positive_int
from .records import build_dashboard_where, filters_for_dashboard


def get_summary(database: Database, query: dict[str, list[str]]) -> dict[str, object]:
    filters = filters_for_dashboard(query)
    where_clause, params = build_dashboard_where(filters)

    with database.connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                COALESCE(SUM(CASE WHEN entry_type = 'income' THEN amount_cents ELSE 0 END), 0) AS income_cents,
                COALESCE(SUM(CASE WHEN entry_type = 'expense' THEN amount_cents ELSE 0 END), 0) AS expense_cents
            FROM financial_records
            WHERE {where_clause}
            """,
            params,
        ).fetchone()

    income_cents = row["income_cents"]
    expense_cents = row["expense_cents"]
    return {
        "filters": filters,
        "totals": {
            "income": money_payload(income_cents),
            "expenses": money_payload(expense_cents),
            "net_balance": money_payload(income_cents - expense_cents),
        },
    }


def get_category_breakdown(database: Database, query: dict[str, list[str]]) -> dict[str, object]:
    filters = filters_for_dashboard(query)
    where_clause, params = build_dashboard_where(filters)

    with database.connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                category,
                entry_type,
                SUM(amount_cents) AS total_cents,
                COUNT(*) AS record_count
            FROM financial_records
            WHERE {where_clause}
            GROUP BY category, entry_type
            ORDER BY total_cents DESC, category ASC
            """,
            params,
        ).fetchall()

    return {
        "filters": filters,
        "categories": [
            {
                "category": row["category"],
                "type": row["entry_type"],
                "total": money_payload(row["total_cents"]),
                "record_count": row["record_count"],
            }
            for row in rows
        ],
    }


def get_trends(database: Database, query: dict[str, list[str]]) -> dict[str, object]:
    filters = filters_for_dashboard(query)
    period = query.get("period", ["month"])[-1] or "month"
    if period not in {"month", "week"}:
        raise ApiError(
            422,
            "Validation failed.",
            code="validation_error",
            details={"period": "Must be either month or week."},
        )

    where_clause, params = build_dashboard_where(filters)
    bucket_expression = (
        "strftime('%Y-%m', entry_date)"
        if period == "month"
        else "printf('%s-W%02d', strftime('%Y', entry_date), CAST(strftime('%W', entry_date) AS INTEGER))"
    )

    with database.connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                {bucket_expression} AS bucket,
                COALESCE(SUM(CASE WHEN entry_type = 'income' THEN amount_cents ELSE 0 END), 0) AS income_cents,
                COALESCE(SUM(CASE WHEN entry_type = 'expense' THEN amount_cents ELSE 0 END), 0) AS expense_cents
            FROM financial_records
            WHERE {where_clause}
            GROUP BY bucket
            ORDER BY bucket ASC
            """,
            params,
        ).fetchall()

    return {
        "period": period,
        "filters": filters,
        "points": [
            {
                "bucket": row["bucket"],
                "income": money_payload(row["income_cents"]),
                "expenses": money_payload(row["expense_cents"]),
                "net_balance": money_payload(row["income_cents"] - row["expense_cents"]),
            }
            for row in rows
        ],
    }


def get_recent_activity(database: Database, query: dict[str, list[str]]) -> dict[str, object]:
    filters = filters_for_dashboard(query)
    where_clause, params = build_dashboard_where(filters)
    limit = parse_positive_int(query.get("limit", [None])[-1], "limit", default=10, minimum=1, maximum=50)

    with database.connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM financial_records
            WHERE {where_clause}
            ORDER BY entry_date DESC, created_at DESC, id DESC
            LIMIT ?
            """,
            [*params, limit],
        ).fetchall()

    return {
        "filters": filters,
        "items": [
            {
                "id": row["id"],
                "amount": money_payload(row["amount_cents"]),
                "type": row["entry_type"],
                "category": row["category"],
                "date": row["entry_date"],
                "notes": row["notes"],
            }
            for row in rows
        ],
    }

