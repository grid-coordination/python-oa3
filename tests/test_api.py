"""Tests for openadr3.api — client and factory functions."""

import pytest

from openadr3.api import (
    BL_SCOPES,
    VEN_SCOPES,
    OpenADRClient,
    body,
    create_bl_client,
    create_ven_client,
    success,
)
from openadr3.entities.models import Program, Ven


class TestSuccess:
    def test_200(self, httpx_mock):
        httpx_mock.add_response(status_code=200)
        client = OpenADRClient(base_url="http://test")
        resp = client._request("GET", "/test")
        assert success(resp)
        client.close()

    def test_404(self, httpx_mock):
        httpx_mock.add_response(status_code=404)
        client = OpenADRClient(base_url="http://test")
        resp = client._request("GET", "/test")
        assert not success(resp)
        client.close()


class TestBody:
    def test_json_body(self, httpx_mock):
        httpx_mock.add_response(json={"key": "value"})
        client = OpenADRClient(base_url="http://test")
        resp = client._request("GET", "/test")
        assert body(resp) == {"key": "value"}
        client.close()


class TestClientPrograms:
    def test_get_programs(self, httpx_mock):
        httpx_mock.add_response(json=[
            {
                "id": "p1",
                "createdDateTime": "2024-06-15T10:00:00Z",
                "modificationDateTime": "2024-06-15T12:00:00Z",
                "objectType": "PROGRAM",
                "programName": "Test",
            }
        ])
        client = OpenADRClient(base_url="http://test")
        programs = client.programs()
        assert len(programs) == 1
        assert programs[0].program_name == "Test"
        assert programs[0]._raw["id"] == "p1"
        client.close()

    def test_get_program_by_id(self, httpx_mock):
        httpx_mock.add_response(json={
            "id": "p1",
            "createdDateTime": "2024-06-15T10:00:00Z",
            "modificationDateTime": "2024-06-15T12:00:00Z",
            "objectType": "PROGRAM",
            "programName": "Test",
        })
        client = OpenADRClient(base_url="http://test")
        p = client.program("p1")
        assert p.program_name == "Test"
        client.close()


    def test_find_program_by_name(self, httpx_mock):
        httpx_mock.add_response(json=[
            {
                "id": "p1",
                "createdDateTime": "2024-06-15T10:00:00Z",
                "modificationDateTime": "2024-06-15T12:00:00Z",
                "objectType": "PROGRAM",
                "programName": "Test",
            }
        ])
        client = OpenADRClient(base_url="http://test")
        p = client.find_program_by_name("Test")
        assert isinstance(p, Program)
        assert p.program_name == "Test"
        client.close()

    def test_find_program_by_name_not_found(self, httpx_mock):
        httpx_mock.add_response(json=[])
        client = OpenADRClient(base_url="http://test")
        p = client.find_program_by_name("Missing")
        assert p is None
        client.close()


class TestClientVens:
    def test_find_ven_by_name(self, httpx_mock):
        httpx_mock.add_response(json=[
            {
                "id": "v1",
                "createdDateTime": "2024-06-15T10:00:00Z",
                "modificationDateTime": "2024-06-15T12:00:00Z",
                "objectType": "VEN",
                "venName": "My VEN",
            }
        ])
        client = OpenADRClient(base_url="http://test")
        v = client.find_ven_by_name("My VEN")
        assert isinstance(v, Ven)
        assert v.ven_name == "My VEN"
        client.close()

    def test_find_ven_by_name_not_found(self, httpx_mock):
        httpx_mock.add_response(json=[])
        client = OpenADRClient(base_url="http://test")
        v = client.find_ven_by_name("Missing")
        assert v is None
        client.close()


class TestClientEvents:
    def test_get_events(self, httpx_mock):
        httpx_mock.add_response(json=[
            {
                "id": "e1",
                "createdDateTime": "2024-06-15T10:00:00Z",
                "modificationDateTime": "2024-06-15T12:00:00Z",
                "objectType": "EVENT",
                "programID": "p1",
                "intervals": [],
            }
        ])
        client = OpenADRClient(base_url="http://test")
        events = client.events()
        assert len(events) == 1
        assert events[0].program_id == "p1"
        client.close()


class TestFactoryFunctions:
    def test_create_ven_client(self):
        c = create_ven_client(base_url="http://test", token="tok")
        assert c.client_type == "ven"
        assert c.scopes == VEN_SCOPES
        c.close()

    def test_create_bl_client(self):
        c = create_bl_client(base_url="http://test", token="tok")
        assert c.client_type == "bl"
        assert c.scopes == BL_SCOPES
        c.close()


class TestContextManager:
    def test_context_manager(self):
        with OpenADRClient(base_url="http://test") as client:
            assert client.base_url == "http://test"
