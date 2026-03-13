"""Entity dispatch — coerce raw API dicts into typed models."""

from __future__ import annotations

import re
from typing import Any

from openadr3.entities.models import (
    Event,
    Notification,
    OpenADRBase,
    Program,
    Report,
    Resource,
    Subscription,
    Ven,
)

_COERCE_REGISTRY: dict[str, type[OpenADRBase]] = {
    "PROGRAM": Program,
    "EVENT": Event,
    "VEN": Ven,
    "BL_VEN_REQUEST": Ven,
    "VEN_VEN_REQUEST": Ven,
    "RESOURCE": Resource,
    "BL_RESOURCE_REQUEST": Resource,
    "VEN_RESOURCE_REQUEST": Resource,
    "REPORT": Report,
    "SUBSCRIPTION": Subscription,
}


def coerce(raw: dict[str, Any]) -> OpenADRBase:
    """Dispatch on objectType and return a coerced entity model.

    Raises KeyError if the objectType is unknown.
    """
    object_type = raw.get("objectType", "")
    model_cls = _COERCE_REGISTRY.get(object_type)
    if model_cls is None:
        raise KeyError(f"Unknown objectType: {object_type!r}")
    return model_cls.from_raw(raw)


def _is_snake_notification(m: dict[str, Any]) -> bool:
    """Check for VTN-RI style snake_case notification (non-spec-compliant)."""
    return "object_type" in m and "operation" in m and "object" in m


def _is_camel_notification(m: dict[str, Any]) -> bool:
    """Check for spec-compliant camelCase notification."""
    return "objectType" in m and "operation" in m and "object" in m


def is_notification(m: dict[str, Any]) -> bool:
    """Check if a dict looks like a notification.

    Handles both spec-compliant camelCase (objectType) and VTN-RI
    snake_case (object_type) formats.
    """
    return _is_camel_notification(m) or _is_snake_notification(m)


# Mapping from snake_case keys to camelCase, with special ID suffix handling
_ID_FIXUPS: dict[str, str] = {
    "program_id": "programID",
    "event_id": "eventID",
    "ven_id": "venID",
    "client_id": "clientID",
    "report_id": "reportID",
    "subscription_id": "subscriptionID",
    "resource_id": "resourceID",
}

_SNAKE_RE = re.compile(r"_([a-z])")


def _snake_to_camel(key: str) -> str:
    """Convert snake_case to camelCase with ID suffix fixups."""
    if key in _ID_FIXUPS:
        return _ID_FIXUPS[key]
    return _SNAKE_RE.sub(lambda m: m.group(1).upper(), key)


def _snake_to_camel_keys(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively convert all keys in a dict from snake_case to camelCase."""
    result = {}
    for k, v in d.items():
        new_key = _snake_to_camel(k)
        if isinstance(v, dict):
            result[new_key] = _snake_to_camel_keys(v)
        elif isinstance(v, list):
            result[new_key] = [
                _snake_to_camel_keys(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            result[new_key] = v
    return result


def coerce_notification(
    raw: dict[str, Any], extra: dict[str, Any] | None = None
) -> Notification:
    """Coerce a notification dict into a Notification.

    Handles both formats:
    - Spec-compliant (camelCase): objectType, operation, object with camelCase keys
    - VTN-RI (snake_case): object_type, operation, object with snake_case keys

    The VTN-RI format is a known bug where MQTT notifications use snake_case
    instead of the camelCase defined in the OpenADR 3 specification.
    """
    is_snake = _is_snake_notification(raw) and not _is_camel_notification(raw)

    if is_snake:
        # VTN-RI snake_case format — convert inner object keys
        object_type = raw["object_type"]
        inner_raw = raw["object"]
        camel_inner = _snake_to_camel_keys(inner_raw)
        if "objectType" not in camel_inner:
            camel_inner["objectType"] = object_type
    else:
        # Spec-compliant camelCase format — inner object already correct
        object_type = raw["objectType"]
        camel_inner = raw["object"]
        if "objectType" not in camel_inner:
            camel_inner["objectType"] = object_type

    coerced_inner = coerce(camel_inner)

    notif = Notification(
        object_type=object_type,
        operation=raw["operation"],
        object=coerced_inner,
        targets=raw.get("targets"),
    )
    notif._raw = raw
    if extra:
        notif._raw = {**raw, **extra}
    return notif
