"""Tests for entity coercion — round-trip for all entity types."""

from decimal import Decimal

import pendulum

from openadr3.entities import coerce, coerce_notification, is_notification
from openadr3.entities.models import (
    Event,
    EventPayloadDescriptor,
    Notification,
    Program,
    Report,
    ReportPayloadDescriptor,
    Resource,
    Subscription,
    Ven,
)


# -- Fixtures: raw API dicts --

RAW_PROGRAM = {
    "id": "prog-001",
    "createdDateTime": "2024-06-15T10:00:00Z",
    "modificationDateTime": "2024-06-15T12:00:00Z",
    "objectType": "PROGRAM",
    "programName": "Test DR Program",
    "intervalPeriod": {
        "start": "2024-06-15T10:00:00Z",
        "duration": "PT1H",
    },
    "programDescriptions": [{"URL": "https://example.com/program"}],
    "payloadDescriptors": [
        {
            "objectType": "EVENT_PAYLOAD_DESCRIPTOR",
            "payloadType": "PRICE",
            "units": "KWH",
            "currency": "USD",
        }
    ],
    "attributes": [{"type": "PRICE", "values": [0.15, 0.25]}],
    "targets": ["target-1"],
}

RAW_EVENT = {
    "id": "evt-001",
    "createdDateTime": "2024-06-15T10:00:00Z",
    "modificationDateTime": "2024-06-15T12:00:00Z",
    "objectType": "EVENT",
    "programID": "prog-001",
    "eventName": "Peak Event",
    "duration": "PT2H",
    "priority": 1,
    "targets": ["target-1"],
    "payloadDescriptors": [
        {
            "objectType": "EVENT_PAYLOAD_DESCRIPTOR",
            "payloadType": "PRICE",
            "units": "KWH",
            "currency": "USD",
        }
    ],
    "intervalPeriod": {
        "start": "2024-06-15T14:00:00Z",
        "duration": "PT2H",
    },
    "intervals": [
        {
            "id": 0,
            "payloads": [{"type": "PRICE", "values": [0.50]}],
        }
    ],
}

RAW_VEN = {
    "id": "ven-001",
    "createdDateTime": "2024-06-15T10:00:00Z",
    "modificationDateTime": "2024-06-15T12:00:00Z",
    "objectType": "VEN",
    "venName": "Test VEN",
    "clientID": "client-123",
    "attributes": [{"type": "USAGE", "values": [100]}],
    "targets": ["target-1"],
}

RAW_RESOURCE = {
    "id": "res-001",
    "createdDateTime": "2024-06-15T10:00:00Z",
    "modificationDateTime": "2024-06-15T12:00:00Z",
    "objectType": "RESOURCE",
    "resourceName": "HVAC Unit 1",
    "venID": "ven-001",
    "clientID": "client-123",
    "targets": ["target-1"],
}

RAW_REPORT = {
    "id": "rpt-001",
    "createdDateTime": "2024-06-15T10:00:00Z",
    "modificationDateTime": "2024-06-15T12:00:00Z",
    "objectType": "REPORT",
    "eventID": "evt-001",
    "clientName": "test-client",
    "clientID": "client-123",
    "reportName": "Usage Report",
    "payloadDescriptors": [
        {
            "objectType": "REPORT_PAYLOAD_DESCRIPTOR",
            "payloadType": "USAGE",
            "readingType": "DIRECT_READ",
            "units": "KWH",
            "accuracy": 0.05,
            "confidence": 95,
        }
    ],
    "resources": [
        {
            "resourceName": "HVAC Unit 1",
            "intervals": [
                {
                    "id": 0,
                    "payloads": [{"type": "USAGE", "values": [42.5]}],
                }
            ],
        }
    ],
}

RAW_SUBSCRIPTION = {
    "id": "sub-001",
    "createdDateTime": "2024-06-15T10:00:00Z",
    "modificationDateTime": "2024-06-15T12:00:00Z",
    "objectType": "SUBSCRIPTION",
    "clientName": "test-client",
    "clientID": "client-123",
    "programID": "prog-001",
    "objectOperations": [
        {
            "objects": ["EVENT"],
            "operations": ["CREATE", "UPDATE"],
            "callbackUrl": "https://example.com/callback",
            "bearerToken": "tok-abc",
        }
    ],
    "targets": ["target-1"],
}


# -- Tests --


class TestCoerceProgram:
    def test_basic_fields(self):
        p = coerce(RAW_PROGRAM)
        assert isinstance(p, Program)
        assert p.id == "prog-001"
        assert p.program_name == "Test DR Program"
        assert p.object_type == "PROGRAM"
        assert p.targets == ["target-1"]

    def test_datetime_coercion(self):
        p = coerce(RAW_PROGRAM)
        assert isinstance(p.created, pendulum.DateTime)
        assert p.created.year == 2024

    def test_interval_period(self):
        p = coerce(RAW_PROGRAM)
        assert p.interval_period is not None
        assert isinstance(p.interval_period.start, pendulum.DateTime)
        assert isinstance(p.interval_period.duration, pendulum.Duration)
        assert p.interval_period.period is not None

    def test_payload_descriptors(self):
        p = coerce(RAW_PROGRAM)
        assert p.payload_descriptors is not None
        assert len(p.payload_descriptors) == 1
        pd = p.payload_descriptors[0]
        assert isinstance(pd, EventPayloadDescriptor)
        assert pd.payload_type == "PRICE"
        assert pd.units == "KWH"
        assert pd.currency == "USD"

    def test_attributes_coerced(self):
        p = coerce(RAW_PROGRAM)
        assert p.attributes is not None
        assert len(p.attributes) == 1
        assert p.attributes[0].type == "price"
        assert p.attributes[0].values == [Decimal("0.15"), Decimal("0.25")]

    def test_raw_preserved(self):
        p = coerce(RAW_PROGRAM)
        assert p._raw == RAW_PROGRAM


class TestCoerceEvent:
    def test_basic_fields(self):
        e = coerce(RAW_EVENT)
        assert isinstance(e, Event)
        assert e.program_id == "prog-001"
        assert e.event_name == "Peak Event"
        assert e.priority == 1

    def test_duration_coercion(self):
        e = coerce(RAW_EVENT)
        assert isinstance(e.duration, pendulum.Duration)
        assert e.duration.hours == 2

    def test_payload_descriptors(self):
        e = coerce(RAW_EVENT)
        assert e.payload_descriptors is not None
        assert len(e.payload_descriptors) == 1
        pd = e.payload_descriptors[0]
        assert isinstance(pd, EventPayloadDescriptor)
        assert pd.payload_type == "PRICE"
        assert pd.units == "KWH"
        assert pd.currency == "USD"

    def test_intervals(self):
        e = coerce(RAW_EVENT)
        assert e.intervals is not None
        assert len(e.intervals) == 1
        assert e.intervals[0].id == 0
        assert e.intervals[0].payloads[0].type == "price"
        assert e.intervals[0].payloads[0].values == [Decimal("0.50")]

    def test_raw_preserved(self):
        e = coerce(RAW_EVENT)
        assert e._raw == RAW_EVENT


class TestCoerceVen:
    def test_basic_fields(self):
        v = coerce(RAW_VEN)
        assert isinstance(v, Ven)
        assert v.ven_name == "Test VEN"
        assert v.client_id == "client-123"

    def test_attributes_coerced(self):
        v = coerce(RAW_VEN)
        assert v.attributes is not None
        assert v.attributes[0].type == "usage"
        assert v.attributes[0].values == [Decimal("100")]

    def test_raw_preserved(self):
        v = coerce(RAW_VEN)
        assert v._raw == RAW_VEN


class TestCoerceResource:
    def test_basic_fields(self):
        r = coerce(RAW_RESOURCE)
        assert isinstance(r, Resource)
        assert r.resource_name == "HVAC Unit 1"
        assert r.ven_id == "ven-001"

    def test_raw_preserved(self):
        r = coerce(RAW_RESOURCE)
        assert r._raw == RAW_RESOURCE


class TestCoerceReport:
    def test_basic_fields(self):
        r = coerce(RAW_REPORT)
        assert isinstance(r, Report)
        assert r.event_id == "evt-001"
        assert r.client_name == "test-client"

    def test_payload_descriptors(self):
        r = coerce(RAW_REPORT)
        assert r.payload_descriptors is not None
        assert len(r.payload_descriptors) == 1
        pd = r.payload_descriptors[0]
        assert isinstance(pd, ReportPayloadDescriptor)
        assert pd.payload_type == "USAGE"
        assert pd.reading_type == "DIRECT_READ"
        assert pd.units == "KWH"
        assert pd.accuracy == 0.05
        assert pd.confidence == 95

    def test_resources(self):
        r = coerce(RAW_REPORT)
        assert len(r.resources) == 1
        assert r.resources[0].resource_name == "HVAC Unit 1"
        assert r.resources[0].intervals[0].payloads[0].type == "usage"
        assert r.resources[0].intervals[0].payloads[0].values == [Decimal("42.5")]

    def test_raw_preserved(self):
        r = coerce(RAW_REPORT)
        assert r._raw == RAW_REPORT


class TestCoerceSubscription:
    def test_basic_fields(self):
        s = coerce(RAW_SUBSCRIPTION)
        assert isinstance(s, Subscription)
        assert s.client_name == "test-client"
        assert s.program_id == "prog-001"

    def test_object_operations(self):
        s = coerce(RAW_SUBSCRIPTION)
        assert len(s.object_operations) == 1
        oo = s.object_operations[0]
        assert oo.objects == ["EVENT"]
        assert oo.operations == ["CREATE", "UPDATE"]
        assert oo.callback_url == "https://example.com/callback"
        assert oo.bearer_token == "tok-abc"

    def test_raw_preserved(self):
        s = coerce(RAW_SUBSCRIPTION)
        assert s._raw == RAW_SUBSCRIPTION


class TestCoerceRequestVariants:
    def test_bl_ven_request(self):
        raw = {**RAW_VEN, "objectType": "BL_VEN_REQUEST"}
        v = coerce(raw)
        assert isinstance(v, Ven)
        assert v.object_type == "BL_VEN_REQUEST"

    def test_ven_resource_request(self):
        raw = {**RAW_RESOURCE, "objectType": "VEN_RESOURCE_REQUEST"}
        r = coerce(raw)
        assert isinstance(r, Resource)


class TestCoerceUnknownType:
    def test_unknown_raises(self):
        import pytest

        with pytest.raises(KeyError):
            coerce({"objectType": "UNKNOWN_THING"})


class TestIsNotification:
    def test_snake_case(self):
        assert is_notification({
            "object_type": "EVENT",
            "operation": "CREATE",
            "object": {"programID": "p1"},
        })

    def test_camel_case(self):
        assert is_notification({
            "objectType": "EVENT",
            "operation": "CREATE",
            "object": {"programID": "p1"},
        })

    def test_false(self):
        assert not is_notification({"objectType": "EVENT"})


class TestCoerceNotification:
    def test_snake_case_vtn_ri(self):
        """VTN-RI sends snake_case keys (non-spec-compliant)."""
        raw_notif = {
            "object_type": "EVENT",
            "operation": "CREATE",
            "object": {
                "id": "evt-002",
                "created_date_time": "2024-06-15T10:00:00Z",
                "modification_date_time": "2024-06-15T12:00:00Z",
                "program_id": "prog-001",
                "event_name": "Notified Event",
                "intervals": [
                    {
                        "id": 0,
                        "payloads": [{"type": "PRICE", "values": [1.00]}],
                    }
                ],
            },
        }
        n = coerce_notification(raw_notif)
        assert isinstance(n, Notification)
        assert n.object_type == "EVENT"
        assert n.operation == "CREATE"
        assert isinstance(n.object, Event)
        assert n.object.event_name == "Notified Event"
        assert n.object.program_id == "prog-001"

    def test_camel_case_spec_compliant(self):
        """Spec-compliant notifications use camelCase throughout."""
        raw_notif = {
            "objectType": "EVENT",
            "operation": "CREATE",
            "object": {
                "id": "evt-003",
                "createdDateTime": "2024-06-15T10:00:00Z",
                "modificationDateTime": "2024-06-15T12:00:00Z",
                "objectType": "EVENT",
                "programID": "prog-001",
                "eventName": "Spec Event",
                "intervals": [
                    {
                        "id": 0,
                        "payloads": [{"type": "PRICE", "values": [2.00]}],
                    }
                ],
            },
        }
        n = coerce_notification(raw_notif)
        assert isinstance(n, Notification)
        assert n.object_type == "EVENT"
        assert n.operation == "CREATE"
        assert isinstance(n.object, Event)
        assert n.object.event_name == "Spec Event"
        assert n.object.program_id == "prog-001"
