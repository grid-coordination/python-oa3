"""Raw Pydantic models mirroring the JSON API shape exactly (camelCase)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RawBase(BaseModel):
    """Base for raw models with camelCase alias support."""

    model_config = ConfigDict(populate_by_name=True)


class RawIntervalPeriod(RawBase):
    start: str | None = None
    duration: str | None = None
    randomize_start: str | None = Field(None, alias="randomizeStart")


class RawValuesMap(RawBase):
    type: str
    values: list[Any]


class RawInterval(RawBase):
    id: int
    interval_period: RawIntervalPeriod | None = Field(None, alias="intervalPeriod")
    payloads: list[RawValuesMap]


class RawEventPayloadDescriptor(RawBase):
    object_type: str = Field(alias="objectType")
    payload_type: str = Field(alias="payloadType")
    units: str | None = None
    currency: str | None = None


class RawReportPayloadDescriptor(RawBase):
    object_type: str = Field(alias="objectType")
    payload_type: str = Field(alias="payloadType")
    reading_type: str | None = Field(None, alias="readingType")
    units: str | None = None
    accuracy: float | None = None
    confidence: int | None = None


class RawReportDescriptor(RawBase):
    payload_type: str = Field(alias="payloadType")
    reading_type: str | None = Field(None, alias="readingType")
    units: str | None = None
    targets: list[str] | None = None
    aggregate: bool = False
    start_interval: int = Field(-1, alias="startInterval")
    num_intervals: int = Field(-1, alias="numIntervals")
    historical: bool = True
    frequency: int = -1
    repeat: int = 1
    report_intervals: str | None = Field(None, alias="reportIntervals")


class RawProgramDescription(RawBase):
    url: str = Field(alias="URL")


class RawProgram(RawBase):
    id: str | None = None
    created_date_time: str | None = Field(None, alias="createdDateTime")
    modification_date_time: str | None = Field(None, alias="modificationDateTime")
    object_type: str = Field("PROGRAM", alias="objectType")
    program_name: str = Field(alias="programName")
    interval_period: RawIntervalPeriod | None = Field(None, alias="intervalPeriod")
    program_descriptions: list[RawProgramDescription] | None = Field(
        None, alias="programDescriptions"
    )
    payload_descriptors: (
        list[RawEventPayloadDescriptor | RawReportPayloadDescriptor] | None
    ) = Field(None, alias="payloadDescriptors")
    attributes: list[RawValuesMap] | None = None
    targets: list[str] | None = None


class RawEvent(RawBase):
    id: str | None = None
    created_date_time: str | None = Field(None, alias="createdDateTime")
    modification_date_time: str | None = Field(None, alias="modificationDateTime")
    object_type: str = Field("EVENT", alias="objectType")
    program_id: str = Field(alias="programID")
    event_name: str | None = Field(None, alias="eventName")
    duration: str | None = None
    priority: int | None = None
    targets: list[str] | None = None
    report_descriptors: list[RawReportDescriptor] | None = Field(
        None, alias="reportDescriptors"
    )
    payload_descriptors: list[RawEventPayloadDescriptor] | None = Field(
        None, alias="payloadDescriptors"
    )
    interval_period: RawIntervalPeriod | None = Field(None, alias="intervalPeriod")
    intervals: list[RawInterval] | None = None


class RawVen(RawBase):
    id: str | None = None
    created_date_time: str | None = Field(None, alias="createdDateTime")
    modification_date_time: str | None = Field(None, alias="modificationDateTime")
    object_type: str = Field("VEN", alias="objectType")
    ven_name: str = Field(alias="venName")
    client_id: str | None = Field(None, alias="clientID")
    attributes: list[RawValuesMap] | None = None
    targets: list[str] | None = None


class RawResource(RawBase):
    id: str | None = None
    created_date_time: str | None = Field(None, alias="createdDateTime")
    modification_date_time: str | None = Field(None, alias="modificationDateTime")
    object_type: str = Field("RESOURCE", alias="objectType")
    resource_name: str = Field(alias="resourceName")
    ven_id: str = Field(alias="venID")
    client_id: str | None = Field(None, alias="clientID")
    attributes: list[RawValuesMap] | None = None
    targets: list[str] | None = None


class RawReportResource(RawBase):
    resource_name: str = Field(alias="resourceName")
    interval_period: RawIntervalPeriod | None = Field(None, alias="intervalPeriod")
    intervals: list[RawInterval]


class RawReport(RawBase):
    id: str | None = None
    created_date_time: str | None = Field(None, alias="createdDateTime")
    modification_date_time: str | None = Field(None, alias="modificationDateTime")
    object_type: str = Field("REPORT", alias="objectType")
    event_id: str = Field(alias="eventID")
    client_name: str = Field(alias="clientName")
    client_id: str | None = Field(None, alias="clientID")
    report_name: str | None = Field(None, alias="reportName")
    payload_descriptors: list[RawReportPayloadDescriptor] | None = Field(
        None, alias="payloadDescriptors"
    )
    resources: list[RawReportResource]


class RawObjectOperation(RawBase):
    objects: list[str]
    operations: list[str]
    callback_url: str = Field(alias="callbackUrl")
    bearer_token: str | None = Field(None, alias="bearerToken")


class RawSubscription(RawBase):
    id: str | None = None
    created_date_time: str | None = Field(None, alias="createdDateTime")
    modification_date_time: str | None = Field(None, alias="modificationDateTime")
    object_type: str = Field("SUBSCRIPTION", alias="objectType")
    client_name: str = Field(alias="clientName")
    client_id: str | None = Field(None, alias="clientID")
    program_id: str | None = Field(None, alias="programID")
    object_operations: list[RawObjectOperation] = Field(alias="objectOperations")
    targets: list[str] | None = None


class RawNotification(RawBase):
    """Notification uses snake_case keys per MQTT convention."""

    object_type: str
    operation: str
    object: dict[str, Any]
    targets: list[str] | None = None
