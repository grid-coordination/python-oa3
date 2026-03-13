"""Payload type dispatch for OpenADR 3 values maps."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def _coerce_price(raw: dict[str, Any]) -> dict[str, Any]:
    """Coerce PRICE payload: values become Decimal."""
    return {
        "type": "price",
        "values": [Decimal(str(v)) for v in raw["values"]],
        "_raw": raw,
    }


def _coerce_usage(raw: dict[str, Any]) -> dict[str, Any]:
    """Coerce USAGE payload: values become Decimal."""
    return {
        "type": "usage",
        "values": [Decimal(str(v)) for v in raw["values"]],
        "_raw": raw,
    }


def _coerce_default(raw: dict[str, Any]) -> dict[str, Any]:
    """Default payload coercion: lowercase type, pass-through values."""
    return {
        "type": raw["type"].lower(),
        "values": raw["values"],
        "_raw": raw,
    }


_PAYLOAD_REGISTRY: dict[str, Any] = {
    "PRICE": _coerce_price,
    "USAGE": _coerce_usage,
}


def coerce_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Coerce a raw valuesMap dict into a payload dict.

    Dispatches on the 'type' field. PRICE and USAGE get Decimal values;
    all others pass through with lowercased type.
    """
    payload_type = raw.get("type", "")
    coercer = _PAYLOAD_REGISTRY.get(payload_type, _coerce_default)
    return coercer(raw)
