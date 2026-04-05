from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def cents_to_amount_string(amount_cents: int) -> str:
    return format((Decimal(amount_cents) / Decimal("100")).quantize(Decimal("0.01")), "f")


def money_payload(amount_cents: int) -> dict[str, int | str]:
    return {
        "amount": cents_to_amount_string(amount_cents),
        "amount_cents": amount_cents,
    }

