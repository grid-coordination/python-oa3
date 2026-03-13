"""openadr3 — OpenADR 3 Entity API Library for Python."""

from openadr3.api import (
    BL_SCOPES,
    VEN_SCOPES,
    OpenADRClient,
    body,
    create_bl_client,
    create_ven_client,
    success,
)
from openadr3.auth import BearerAuth, fetch_token
from openadr3.entities import coerce, coerce_notification, is_notification
from openadr3.entities.models import (
    Event,
    Interval,
    IntervalPeriod,
    Notification,
    ObjectOperation,
    OpenADRBase,
    Payload,
    Program,
    Report,
    ReportResource,
    Resource,
    Subscription,
    Ven,
)
from openadr3.enums import ObjectType, Operation, PayloadType
from openadr3.time import (
    PendulumDateTime,
    PendulumDuration,
    parse_datetime,
    parse_duration,
    to_zoned,
)

__all__ = [
    # API client
    "OpenADRClient",
    "create_ven_client",
    "create_bl_client",
    "success",
    "body",
    "BearerAuth",
    "fetch_token",
    "VEN_SCOPES",
    "BL_SCOPES",
    # Entity dispatch
    "coerce",
    "coerce_notification",
    "is_notification",
    # Entity models
    "OpenADRBase",
    "Program",
    "Event",
    "Ven",
    "Resource",
    "Report",
    "ReportResource",
    "Subscription",
    "Notification",
    "Interval",
    "IntervalPeriod",
    "Payload",
    "ObjectOperation",
    # Enums
    "ObjectType",
    "Operation",
    "PayloadType",
    # Time utilities
    "PendulumDateTime",
    "PendulumDuration",
    "parse_datetime",
    "parse_duration",
    "to_zoned",
]
