from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from .errors import ApiError, validation_error


ROLE_VALUES = {"viewer", "analyst", "admin"}
STATUS_VALUES = {"active", "inactive"}
RECORD_TYPE_VALUES = {"income", "expense"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def ensure_json_object(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ApiError(400, "Request body must be a JSON object.", code="invalid_body")
    return payload


def require_non_empty_string(
    value: object,
    field_name: str,
    *,
    min_length: int = 1,
    max_length: int = 255,
) -> str:
    if not isinstance(value, str):
        raise validation_error({field_name: "Must be a string."})
    cleaned = value.strip()
    if len(cleaned) < min_length:
        raise validation_error({field_name: f"Must be at least {min_length} characters long."})
    if len(cleaned) > max_length:
        raise validation_error({field_name: f"Must be at most {max_length} characters long."})
    return cleaned


def optional_string(
    value: object,
    field_name: str,
    *,
    max_length: int = 255,
) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise validation_error({field_name: "Must be a string."})
    cleaned = value.strip()
    if len(cleaned) > max_length:
        raise validation_error({field_name: f"Must be at most {max_length} characters long."})
    return cleaned


def validate_email(value: object, field_name: str = "email") -> str:
    email = require_non_empty_string(value, field_name, max_length=255).lower()
    if not EMAIL_PATTERN.match(email):
        raise validation_error({field_name: "Must be a valid email address."})
    return email


def validate_password(value: object, field_name: str = "password") -> str:
    return require_non_empty_string(value, field_name, min_length=8, max_length=128)


def validate_role(value: object, field_name: str = "role") -> str:
    if not isinstance(value, str):
        raise validation_error({field_name: "Must be one of: viewer, analyst, admin."})
    role = value.strip().lower()
    if role not in ROLE_VALUES:
        raise validation_error({field_name: "Must be one of: viewer, analyst, admin."})
    return role


def validate_status(value: object, field_name: str = "status") -> str:
    if not isinstance(value, str):
        raise validation_error({field_name: "Must be one of: active, inactive."})
    status = value.strip().lower()
    if status not in STATUS_VALUES:
        raise validation_error({field_name: "Must be one of: active, inactive."})
    return status


def validate_record_type(value: object, field_name: str = "type") -> str:
    if not isinstance(value, str):
        raise validation_error({field_name: "Must be either income or expense."})
    record_type = value.strip().lower()
    if record_type not in RECORD_TYPE_VALUES:
        raise validation_error({field_name: "Must be either income or expense."})
    return record_type


def validate_iso_date(value: object, field_name: str = "date") -> str:
    if not isinstance(value, str):
        raise validation_error({field_name: "Must be an ISO date in YYYY-MM-DD format."})
    cleaned = value.strip()
    try:
        return date.fromisoformat(cleaned).isoformat()
    except ValueError as exc:
        raise validation_error({field_name: "Must be an ISO date in YYYY-MM-DD format."}) from exc


def parse_amount_to_cents(value: object, field_name: str = "amount") -> int:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise validation_error({field_name: "Must be a positive number with up to two decimal places."}) from exc

    if decimal_value <= 0:
        raise validation_error({field_name: "Must be greater than zero."})

    quantized = decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if quantized != decimal_value:
        raise validation_error({field_name: "Must have at most two decimal places."})
    return int(quantized * 100)


def parse_positive_int(
    value: str | None,
    field_name: str,
    *,
    default: int,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise validation_error({field_name: "Must be an integer."}) from exc
    if parsed < minimum:
        raise validation_error({field_name: f"Must be greater than or equal to {minimum}."})
    if maximum is not None and parsed > maximum:
        raise validation_error({field_name: f"Must be less than or equal to {maximum}."})
    return parsed


def parse_identifier(value: str, field_name: str = "id") -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ApiError(404, "Resource not found.", code="not_found") from exc
    if parsed <= 0:
        raise ApiError(404, "Resource not found.", code="not_found")
    return parsed
