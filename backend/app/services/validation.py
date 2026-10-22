"""Reusable payload validators shared by all services (no Flask imports).

Each helper reads one field from a JSON payload, checks its type and value,
and returns the cleaned value or raises ValidationError with a clear message.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.errors import ValidationError

# Sentinel to tell "field not sent" apart from "field sent as null"
_MISSING = object()

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"


def require_object(payload: Any) -> Mapping[str, Any]:
    """Ensure the request body is a JSON object."""
    if not isinstance(payload, Mapping):
        raise ValidationError("Request body must be a JSON object")
    return payload


def require_str(payload: Mapping[str, Any], field: str) -> str:
    """Return a required, non-blank string (surrounding spaces removed)."""
    value = payload.get(field, _MISSING)
    if value is _MISSING or value is None:
        raise ValidationError(f"'{field}' is required")
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"'{field}' must be a non-empty string")
    return value.strip()


def require_positive_int(payload: Mapping[str, Any], field: str) -> int:
    """Return a required integer strictly greater than 0."""
    value = payload.get(field, _MISSING)
    if value is _MISSING or value is None:
        raise ValidationError(f"'{field}' is required")
    # bool is a subclass of int in Python: reject true/false explicitly
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"'{field}' must be an integer")
    if value <= 0:
        raise ValidationError(f"'{field}' must be greater than 0")
    return value


def optional_str_list(payload: Mapping[str, Any], field: str) -> list[str]:
    """Return a list of non-blank strings; missing or null means an empty list."""
    value = payload.get(field)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError(f"'{field}' must be a list of strings")

    items = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"'{field}' must only contain non-empty strings")
        items.append(item.strip())
    return items


def _require_formatted(payload: Mapping[str, Any], field: str, fmt: str, expected: str) -> str:
    """Parse a string with a strptime format and return it normalized to that format."""
    value = payload.get(field, _MISSING)
    if value is _MISSING or value is None:
        raise ValidationError(f"'{field}' is required")
    try:
        if not isinstance(value, str):
            raise ValueError
        return datetime.strptime(value.strip(), fmt).strftime(fmt)
    except ValueError:
        raise ValidationError(f"'{field}' must be a valid {expected}") from None


def require_date(payload: Mapping[str, Any], field: str) -> str:
    """Return a required date as 'YYYY-MM-DD' (rejects impossible dates like 2026-02-30)."""
    return _require_formatted(payload, field, DATE_FORMAT, "date (YYYY-MM-DD)")


def require_time(payload: Mapping[str, Any], field: str) -> str:
    """Return a required time as zero-padded 'HH:MM' (so strings compare chronologically)."""
    return _require_formatted(payload, field, TIME_FORMAT, "time (HH:MM)")
