"""Pendulum-based time parsing and Pydantic annotated types for OpenADR 3."""

from __future__ import annotations

from typing import Annotated, Any

import pendulum
from pydantic import BeforeValidator, PlainSerializer


def parse_datetime(s: Any) -> pendulum.DateTime | None:
    """Parse RFC 3339 datetime string, handling VTN-RI non-standard formats.

    Handles both standard ISO 8601 (with 'T') and non-standard formats
    where 'T' is replaced by a space.
    """
    if s is None:
        return None
    if isinstance(s, pendulum.DateTime):
        return s
    if not isinstance(s, str):
        raise ValueError(f"Expected string or None, got {type(s)}")
    # Handle non-standard format: space instead of T
    s = s.strip()
    if not s:
        return None
    return pendulum.parse(s, strict=False)


def parse_duration(s: Any) -> pendulum.Duration | None:
    """Parse ISO 8601 duration string."""
    if s is None:
        return None
    if isinstance(s, pendulum.Duration):
        return s
    if not isinstance(s, str):
        raise ValueError(f"Expected string or None, got {type(s)}")
    s = s.strip()
    if not s:
        return None
    return pendulum.parse(s, exact=True)


def to_zoned(dt: pendulum.DateTime, tz: str) -> pendulum.DateTime:
    """Convert a datetime to the given timezone."""
    return dt.in_tz(pendulum.timezone(tz))


def _validate_datetime(v: Any) -> pendulum.DateTime | None:
    return parse_datetime(v)


def _serialize_datetime(v: pendulum.DateTime | None) -> str | None:
    if v is None:
        return None
    return v.to_iso8601_string()


def _validate_duration(v: Any) -> pendulum.Duration | None:
    return parse_duration(v)


def _serialize_duration(v: pendulum.Duration | None) -> str | None:
    if v is None:
        return None
    # Build ISO 8601 duration string
    parts = []
    years = getattr(v, "years", 0)
    months = getattr(v, "months", 0)
    weeks = getattr(v, "weeks", 0)
    days = getattr(v, "remaining_days", 0)
    hours = getattr(v, "hours", 0)
    minutes = getattr(v, "minutes", 0)
    seconds = getattr(v, "remaining_seconds", 0)

    parts.append("P")
    if years:
        parts.append(f"{years}Y")
    if months:
        parts.append(f"{months}M")
    if weeks:
        parts.append(f"{weeks}W")
    if days:
        parts.append(f"{days}D")
    time_parts = []
    if hours:
        time_parts.append(f"{hours}H")
    if minutes:
        time_parts.append(f"{minutes}M")
    if seconds:
        time_parts.append(f"{seconds}S")
    if time_parts:
        parts.append("T")
        parts.extend(time_parts)
    result = "".join(parts)
    return result if result != "P" else "PT0S"


PendulumDateTime = Annotated[
    pendulum.DateTime | None,
    BeforeValidator(_validate_datetime),
    PlainSerializer(_serialize_datetime),
]

PendulumDuration = Annotated[
    pendulum.Duration | None,
    BeforeValidator(_validate_duration),
    PlainSerializer(_serialize_duration),
]
