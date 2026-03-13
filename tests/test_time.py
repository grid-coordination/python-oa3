"""Tests for openadr3.time — datetime/duration parsing and annotated types."""

import pendulum
import pytest

from openadr3.time import parse_datetime, parse_duration, to_zoned


class TestParseDatetime:
    def test_rfc3339(self):
        dt = parse_datetime("2024-06-15T10:30:00Z")
        assert isinstance(dt, pendulum.DateTime)
        assert dt.year == 2024
        assert dt.month == 6
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30

    def test_with_offset(self):
        dt = parse_datetime("2024-06-15T10:30:00-05:00")
        assert isinstance(dt, pendulum.DateTime)
        assert dt.offset_hours == -5

    def test_non_standard_space_with_tz(self):
        dt = parse_datetime("2024-06-15 10:30:00Z")
        assert isinstance(dt, pendulum.DateTime)
        assert dt.hour == 10

    def test_vtn_ri_mqtt_format(self):
        """VTN-RI MQTT notifications use space separator and no timezone.

        See oadr3-org/openadr3-vtn-reference-implementation#180 (issue #3).
        """
        dt = parse_datetime("2026-03-08 19:22:06")
        assert isinstance(dt, pendulum.DateTime)
        assert dt.year == 2026
        assert dt.month == 3
        assert dt.day == 8
        assert dt.hour == 19
        assert dt.minute == 22
        assert dt.second == 6

    def test_none(self):
        assert parse_datetime(None) is None

    def test_empty_string(self):
        assert parse_datetime("") is None

    def test_passthrough(self):
        original = pendulum.now("UTC")
        assert parse_datetime(original) is original

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            parse_datetime(42)


class TestParseDuration:
    def test_iso8601_hours(self):
        d = parse_duration("PT1H")
        assert isinstance(d, pendulum.Duration)
        assert d.hours == 1

    def test_iso8601_complex(self):
        d = parse_duration("P1DT2H30M")
        assert isinstance(d, pendulum.Duration)
        assert d.remaining_days == 1
        assert d.hours == 2
        assert d.minutes == 30

    def test_none(self):
        assert parse_duration(None) is None

    def test_empty_string(self):
        assert parse_duration("") is None

    def test_passthrough(self):
        original = pendulum.duration(hours=5)
        assert parse_duration(original) is original

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            parse_duration(123)


class TestToZoned:
    def test_utc_to_eastern(self):
        utc = pendulum.parse("2024-06-15T14:00:00Z")
        eastern = to_zoned(utc, "America/New_York")
        assert eastern.timezone_name == "America/New_York"
        assert eastern.hour == 10  # EDT = UTC-4
