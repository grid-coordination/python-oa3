"""Coerced Pydantic models — snake_case fields with pendulum types."""

from __future__ import annotations

from typing import Any

import pendulum
from pydantic import BaseModel, ConfigDict, PrivateAttr

from openadr3.entities.payloads import coerce_payload
from openadr3.time import PendulumDateTime, PendulumDuration, parse_datetime, parse_duration


class OpenADRBase(BaseModel):
    """Base model for all coerced OpenADR entities.

    Carries the original raw dict as a private attribute.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "OpenADRBase":
        """Create an instance from a raw API dict, preserving the original."""
        raise NotImplementedError("Subclasses must implement from_raw")


class Payload(BaseModel):
    """A coerced values map / payload."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: str
    values: list[Any]
    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Payload:
        coerced = coerce_payload(raw)
        raw_dict = coerced.pop("_raw", raw)
        inst = cls(type=coerced["type"], values=coerced["values"])
        inst._raw = raw_dict
        return inst


class IntervalPeriod(BaseModel):
    """Coerced interval period with pendulum types and computed period."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    start: PendulumDateTime = None
    duration: PendulumDuration = None
    randomize_start: PendulumDuration = None
    period: tuple[pendulum.DateTime, pendulum.DateTime] | None = None
    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> IntervalPeriod:
        start = parse_datetime(raw.get("start"))
        duration = parse_duration(raw.get("duration"))
        randomize_start = parse_duration(raw.get("randomizeStart"))

        period = None
        if start is not None and duration is not None:
            end = start.add(
                years=getattr(duration, "years", 0),
                months=getattr(duration, "months", 0),
                weeks=getattr(duration, "weeks", 0),
                days=getattr(duration, "remaining_days", 0),
                hours=getattr(duration, "hours", 0),
                minutes=getattr(duration, "minutes", 0),
                seconds=getattr(duration, "remaining_seconds", 0),
            )
            period = (start, end)

        inst = cls(
            start=start,
            duration=duration,
            randomize_start=randomize_start,
            period=period,
        )
        inst._raw = raw
        return inst


class Interval(BaseModel):
    """Coerced interval with payloads."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    interval_period: IntervalPeriod | None = None
    payloads: list[Payload]
    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Interval:
        ip = raw.get("intervalPeriod")
        inst = cls(
            id=raw["id"],
            interval_period=IntervalPeriod.from_raw(ip) if ip else None,
            payloads=[Payload.from_raw(p) for p in raw.get("payloads", [])],
        )
        inst._raw = raw
        return inst


def _parse_interval_period(raw: dict[str, Any], key: str = "intervalPeriod") -> IntervalPeriod | None:
    ip = raw.get(key)
    return IntervalPeriod.from_raw(ip) if ip else None


def _parse_intervals(raw: dict[str, Any]) -> list[Interval] | None:
    intervals = raw.get("intervals")
    if intervals is None:
        return None
    return [Interval.from_raw(i) for i in intervals]


class Program(OpenADRBase):
    id: str | None = None
    created: PendulumDateTime = None
    modified: PendulumDateTime = None
    object_type: str = "PROGRAM"
    program_name: str
    interval_period: IntervalPeriod | None = None
    descriptions: list[dict[str, Any]] | None = None
    payload_descriptors: list[dict[str, Any]] | None = None
    attributes: list[Payload] | None = None
    targets: list[str] | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Program:
        attrs = raw.get("attributes")
        inst = cls(
            id=raw.get("id"),
            created=raw.get("createdDateTime"),
            modified=raw.get("modificationDateTime"),
            object_type=raw.get("objectType", "PROGRAM"),
            program_name=raw["programName"],
            interval_period=_parse_interval_period(raw),
            descriptions=raw.get("programDescriptions"),
            payload_descriptors=raw.get("payloadDescriptors"),
            attributes=[Payload.from_raw(a) for a in attrs] if attrs else None,
            targets=raw.get("targets"),
        )
        inst._raw = raw
        return inst


class Event(OpenADRBase):
    id: str | None = None
    created: PendulumDateTime = None
    modified: PendulumDateTime = None
    object_type: str = "EVENT"
    program_id: str
    event_name: str | None = None
    duration: PendulumDuration = None
    priority: int | None = None
    targets: list[str] | None = None
    report_descriptors: list[dict[str, Any]] | None = None
    payload_descriptors: list[dict[str, Any]] | None = None
    interval_period: IntervalPeriod | None = None
    intervals: list[Interval] | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Event:
        inst = cls(
            id=raw.get("id"),
            created=raw.get("createdDateTime"),
            modified=raw.get("modificationDateTime"),
            object_type=raw.get("objectType", "EVENT"),
            program_id=raw["programID"],
            event_name=raw.get("eventName"),
            duration=raw.get("duration"),
            priority=raw.get("priority"),
            targets=raw.get("targets"),
            report_descriptors=raw.get("reportDescriptors"),
            payload_descriptors=raw.get("payloadDescriptors"),
            interval_period=_parse_interval_period(raw),
            intervals=_parse_intervals(raw),
        )
        inst._raw = raw
        return inst


class Ven(OpenADRBase):
    id: str | None = None
    created: PendulumDateTime = None
    modified: PendulumDateTime = None
    object_type: str = "VEN"
    ven_name: str
    client_id: str | None = None
    attributes: list[Payload] | None = None
    targets: list[str] | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Ven:
        attrs = raw.get("attributes")
        inst = cls(
            id=raw.get("id"),
            created=raw.get("createdDateTime"),
            modified=raw.get("modificationDateTime"),
            object_type=raw.get("objectType", "VEN"),
            ven_name=raw["venName"],
            client_id=raw.get("clientID"),
            attributes=[Payload.from_raw(a) for a in attrs] if attrs else None,
            targets=raw.get("targets"),
        )
        inst._raw = raw
        return inst


class Resource(OpenADRBase):
    id: str | None = None
    created: PendulumDateTime = None
    modified: PendulumDateTime = None
    object_type: str = "RESOURCE"
    resource_name: str
    ven_id: str
    client_id: str | None = None
    attributes: list[Payload] | None = None
    targets: list[str] | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Resource:
        attrs = raw.get("attributes")
        inst = cls(
            id=raw.get("id"),
            created=raw.get("createdDateTime"),
            modified=raw.get("modificationDateTime"),
            object_type=raw.get("objectType", "RESOURCE"),
            resource_name=raw["resourceName"],
            ven_id=raw["venID"],
            client_id=raw.get("clientID"),
            attributes=[Payload.from_raw(a) for a in attrs] if attrs else None,
            targets=raw.get("targets"),
        )
        inst._raw = raw
        return inst


class ReportResource(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    resource_name: str
    interval_period: IntervalPeriod | None = None
    intervals: list[Interval]
    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> ReportResource:
        inst = cls(
            resource_name=raw["resourceName"],
            interval_period=_parse_interval_period(raw),
            intervals=[Interval.from_raw(i) for i in raw.get("intervals", [])],
        )
        inst._raw = raw
        return inst


class Report(OpenADRBase):
    id: str | None = None
    created: PendulumDateTime = None
    modified: PendulumDateTime = None
    object_type: str = "REPORT"
    event_id: str
    client_name: str
    client_id: str | None = None
    report_name: str | None = None
    payload_descriptors: list[dict[str, Any]] | None = None
    resources: list[ReportResource]

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Report:
        inst = cls(
            id=raw.get("id"),
            created=raw.get("createdDateTime"),
            modified=raw.get("modificationDateTime"),
            object_type=raw.get("objectType", "REPORT"),
            event_id=raw["eventID"],
            client_name=raw["clientName"],
            client_id=raw.get("clientID"),
            report_name=raw.get("reportName"),
            payload_descriptors=raw.get("payloadDescriptors"),
            resources=[ReportResource.from_raw(r) for r in raw["resources"]],
        )
        inst._raw = raw
        return inst


class ObjectOperation(BaseModel):
    objects: list[str]
    operations: list[str]
    callback_url: str
    bearer_token: str | None = None
    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> ObjectOperation:
        inst = cls(
            objects=raw["objects"],
            operations=raw["operations"],
            callback_url=raw["callbackUrl"],
            bearer_token=raw.get("bearerToken"),
        )
        inst._raw = raw
        return inst


class Subscription(OpenADRBase):
    id: str | None = None
    created: PendulumDateTime = None
    modified: PendulumDateTime = None
    object_type: str = "SUBSCRIPTION"
    client_name: str
    client_id: str | None = None
    program_id: str | None = None
    object_operations: list[ObjectOperation]
    targets: list[str] | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Subscription:
        inst = cls(
            id=raw.get("id"),
            created=raw.get("createdDateTime"),
            modified=raw.get("modificationDateTime"),
            object_type=raw.get("objectType", "SUBSCRIPTION"),
            client_name=raw["clientName"],
            client_id=raw.get("clientID"),
            program_id=raw.get("programID"),
            object_operations=[
                ObjectOperation.from_raw(oo) for oo in raw["objectOperations"]
            ],
            targets=raw.get("targets"),
        )
        inst._raw = raw
        return inst


class Notification(BaseModel):
    """Coerced notification — inner object is a coerced entity."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    object_type: str
    operation: str
    object: OpenADRBase
    targets: list[str] | None = None
    _raw: dict[str, Any] = PrivateAttr(default_factory=dict)
