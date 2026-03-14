"""OpenADR 3 API client — spec-driven HTTP with entity coercion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import yaml

from openadr3.auth import BearerAuth
from openadr3.entities import coerce
from openadr3.entities.models import (
    Event,
    OpenADRBase,
    Program,
    Report,
    Resource,
    Subscription,
    Ven,
)

# Client type scopes matching Clojure implementation
VEN_SCOPES = frozenset({
    "read_all",
    "read_targets",
    "read_ven_objects",
    "write_reports",
    "write_subscriptions",
    "write_vens",
})

BL_SCOPES = frozenset({
    "read_all",
    "read_bl",
    "write_programs",
    "write_events",
    "write_subscriptions",
    "write_vens",
})


def success(resp: httpx.Response) -> bool:
    """Check if an HTTP response indicates success (2xx)."""
    return 200 <= resp.status_code < 300


def body(resp: httpx.Response) -> Any:
    """Extract JSON body from a response."""
    return resp.json()


class OpenADRClient:
    """Spec-aware OpenADR 3 HTTP client.

    Wraps httpx.Client with optional OpenAPI spec validation,
    raw CRUD methods (returning httpx.Response), and coerced
    convenience methods (returning entity models).
    """

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        spec_path: str | Path | None = None,
        client_type: str | None = None,
        scopes: frozenset[str] | None = None,
        validate: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_type = client_type
        self.scopes = scopes or frozenset()
        self.validate = validate
        self._spec: dict[str, Any] | None = None

        if spec_path:
            self._spec = self._load_spec(spec_path)

        auth = BearerAuth(token) if token else None
        self._http = httpx.Client(base_url=self.base_url, auth=auth)

    @staticmethod
    def _load_spec(path: str | Path) -> dict[str, Any]:
        with open(path) as f:
            return yaml.safe_load(f)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> OpenADRClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # -- Introspection --

    def all_routes(self) -> list[str]:
        """Return all path templates from the OpenAPI spec."""
        if not self._spec:
            return []
        return list(self._spec.get("paths", {}).keys())

    def endpoint_scopes(self, path: str, method: str = "get") -> list[str]:
        """Return OAuth2 scopes required for a specific endpoint."""
        if not self._spec:
            return []
        path_item = self._spec.get("paths", {}).get(path, {})
        operation = path_item.get(method, {})
        security = operation.get("security", [])
        scopes_list = []
        for sec in security:
            for _scheme, scope_list in sec.items():
                scopes_list.extend(scope_list)
        return scopes_list

    def authorized(self, path: str, method: str = "get") -> bool:
        """Check if this client's scopes authorize a given endpoint."""
        required = set(self.endpoint_scopes(path, method))
        if not required:
            return True
        return bool(self.scopes & required)

    # -- Core HTTP --

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request."""
        return self._http.request(method, path, params=params, json=json)

    # -- Raw CRUD: Programs --

    def get_programs(self, **params: Any) -> httpx.Response:
        return self._request("GET", "/programs", params=params or None)

    def get_program_by_id(self, program_id: str) -> httpx.Response:
        return self._request("GET", f"/programs/{program_id}")

    def create_program(self, data: dict[str, Any]) -> httpx.Response:
        return self._request("POST", "/programs", json=data)

    def update_program(self, program_id: str, data: dict[str, Any]) -> httpx.Response:
        return self._request("PUT", f"/programs/{program_id}", json=data)

    def delete_program(self, program_id: str) -> httpx.Response:
        return self._request("DELETE", f"/programs/{program_id}")

    # -- Raw CRUD: Events --

    def get_events(self, **params: Any) -> httpx.Response:
        return self._request("GET", "/events", params=params or None)

    def get_event_by_id(self, event_id: str) -> httpx.Response:
        return self._request("GET", f"/events/{event_id}")

    def create_event(self, data: dict[str, Any]) -> httpx.Response:
        return self._request("POST", "/events", json=data)

    def update_event(self, event_id: str, data: dict[str, Any]) -> httpx.Response:
        return self._request("PUT", f"/events/{event_id}", json=data)

    def delete_event(self, event_id: str) -> httpx.Response:
        return self._request("DELETE", f"/events/{event_id}")

    # -- Raw CRUD: VENs --

    def get_vens(self, **params: Any) -> httpx.Response:
        return self._request("GET", "/vens", params=params or None)

    def get_ven_by_id(self, ven_id: str) -> httpx.Response:
        return self._request("GET", f"/vens/{ven_id}")

    def create_ven(self, data: dict[str, Any]) -> httpx.Response:
        return self._request("POST", "/vens", json=data)

    def update_ven(self, ven_id: str, data: dict[str, Any]) -> httpx.Response:
        return self._request("PUT", f"/vens/{ven_id}", json=data)

    def delete_ven(self, ven_id: str) -> httpx.Response:
        return self._request("DELETE", f"/vens/{ven_id}")

    # -- Raw CRUD: Resources --

    def get_resources(self, **params: Any) -> httpx.Response:
        return self._request("GET", "/resources", params=params or None)

    def get_resource_by_id(self, resource_id: str) -> httpx.Response:
        return self._request("GET", f"/resources/{resource_id}")

    def create_resource(self, data: dict[str, Any]) -> httpx.Response:
        return self._request("POST", "/resources", json=data)

    def update_resource(self, resource_id: str, data: dict[str, Any]) -> httpx.Response:
        return self._request("PUT", f"/resources/{resource_id}", json=data)

    def delete_resource(self, resource_id: str) -> httpx.Response:
        return self._request("DELETE", f"/resources/{resource_id}")

    # -- Raw CRUD: Reports --

    def get_reports(self, **params: Any) -> httpx.Response:
        return self._request("GET", "/reports", params=params or None)

    def get_report_by_id(self, report_id: str) -> httpx.Response:
        return self._request("GET", f"/reports/{report_id}")

    def create_report(self, data: dict[str, Any]) -> httpx.Response:
        return self._request("POST", "/reports", json=data)

    def update_report(self, report_id: str, data: dict[str, Any]) -> httpx.Response:
        return self._request("PUT", f"/reports/{report_id}", json=data)

    def delete_report(self, report_id: str) -> httpx.Response:
        return self._request("DELETE", f"/reports/{report_id}")

    # -- Raw CRUD: Subscriptions --

    def get_subscriptions(self, **params: Any) -> httpx.Response:
        return self._request("GET", "/subscriptions", params=params or None)

    def get_subscription_by_id(self, subscription_id: str) -> httpx.Response:
        return self._request("GET", f"/subscriptions/{subscription_id}")

    def create_subscription(self, data: dict[str, Any]) -> httpx.Response:
        return self._request("POST", "/subscriptions", json=data)

    def update_subscription(
        self, subscription_id: str, data: dict[str, Any]
    ) -> httpx.Response:
        return self._request("PUT", f"/subscriptions/{subscription_id}", json=data)

    def delete_subscription(self, subscription_id: str) -> httpx.Response:
        return self._request("DELETE", f"/subscriptions/{subscription_id}")

    # -- Notifiers & MQTT Topics --

    def get_notifiers(self) -> httpx.Response:
        return self._request("GET", "/notifiers")

    def get_mqtt_topics_programs(self) -> httpx.Response:
        return self._request("GET", "/notifiers/mqtt/topics/programs")

    def get_mqtt_topics_program(self, program_id: str) -> httpx.Response:
        return self._request("GET", f"/notifiers/mqtt/topics/programs/{program_id}")

    def get_mqtt_topics_program_events(self, program_id: str) -> httpx.Response:
        return self._request("GET", f"/notifiers/mqtt/topics/programs/{program_id}/events")

    def get_mqtt_topics_events(self) -> httpx.Response:
        return self._request("GET", "/notifiers/mqtt/topics/events")

    def get_mqtt_topics_reports(self) -> httpx.Response:
        return self._request("GET", "/notifiers/mqtt/topics/reports")

    def get_mqtt_topics_subscriptions(self) -> httpx.Response:
        return self._request("GET", "/notifiers/mqtt/topics/subscriptions")

    def get_mqtt_topics_vens(self) -> httpx.Response:
        return self._request("GET", "/notifiers/mqtt/topics/vens")

    def get_mqtt_topics_ven(self, ven_id: str) -> httpx.Response:
        return self._request("GET", f"/notifiers/mqtt/topics/vens/{ven_id}")

    def get_mqtt_topics_ven_events(self, ven_id: str) -> httpx.Response:
        return self._request("GET", f"/notifiers/mqtt/topics/vens/{ven_id}/events")

    def get_mqtt_topics_ven_programs(self, ven_id: str) -> httpx.Response:
        return self._request("GET", f"/notifiers/mqtt/topics/vens/{ven_id}/programs")

    def get_mqtt_topics_ven_resources(self, ven_id: str) -> httpx.Response:
        return self._request("GET", f"/notifiers/mqtt/topics/vens/{ven_id}/resources")

    def get_mqtt_topics_resources(self) -> httpx.Response:
        return self._request("GET", "/notifiers/mqtt/topics/resources")

    # -- VEN lookup --

    def find_ven_by_name(self, name: str) -> dict[str, Any] | None:
        """Find a VEN by venName. Returns the raw dict or None."""
        resp = self.get_vens(targetType="VEN_NAME", targetValues=[name])
        if not success(resp):
            return None
        for v in resp.json():
            if v.get("venName") == name:
                return v
        return None

    # -- Coerced entity methods --

    def _coerce_list(self, resp: httpx.Response) -> list[OpenADRBase]:
        """Coerce a list response into entity models."""
        resp.raise_for_status()
        return [coerce(item) for item in resp.json()]

    def _coerce_one(self, resp: httpx.Response) -> OpenADRBase:
        """Coerce a single-item response into an entity model."""
        resp.raise_for_status()
        return coerce(resp.json())

    def programs(self, **params: Any) -> list[Program]:
        return self._coerce_list(self.get_programs(**params))  # type: ignore[return-value]

    def program(self, program_id: str) -> Program:
        return self._coerce_one(self.get_program_by_id(program_id))  # type: ignore[return-value]

    def events(self, **params: Any) -> list[Event]:
        return self._coerce_list(self.get_events(**params))  # type: ignore[return-value]

    def event(self, event_id: str) -> Event:
        return self._coerce_one(self.get_event_by_id(event_id))  # type: ignore[return-value]

    def vens(self, **params: Any) -> list[Ven]:
        return self._coerce_list(self.get_vens(**params))  # type: ignore[return-value]

    def ven(self, ven_id: str) -> Ven:
        return self._coerce_one(self.get_ven_by_id(ven_id))  # type: ignore[return-value]

    def resources(self, **params: Any) -> list[Resource]:
        return self._coerce_list(self.get_resources(**params))  # type: ignore[return-value]

    def resource(self, resource_id: str) -> Resource:
        return self._coerce_one(self.get_resource_by_id(resource_id))  # type: ignore[return-value]

    def reports(self, **params: Any) -> list[Report]:
        return self._coerce_list(self.get_reports(**params))  # type: ignore[return-value]

    def report(self, report_id: str) -> Report:
        return self._coerce_one(self.get_report_by_id(report_id))  # type: ignore[return-value]

    def subscriptions(self, **params: Any) -> list[Subscription]:
        return self._coerce_list(self.get_subscriptions(**params))  # type: ignore[return-value]

    def subscription(self, subscription_id: str) -> Subscription:
        return self._coerce_one(self.get_subscription_by_id(subscription_id))  # type: ignore[return-value]


def create_ven_client(
    base_url: str,
    token: str,
    spec_path: str | Path | None = None,
    validate: bool = False,
) -> OpenADRClient:
    """Create an OpenADR client configured for VEN operations."""
    return OpenADRClient(
        base_url=base_url,
        token=token,
        spec_path=spec_path,
        client_type="ven",
        scopes=VEN_SCOPES,
        validate=validate,
    )


def create_bl_client(
    base_url: str,
    token: str,
    spec_path: str | Path | None = None,
    validate: bool = False,
) -> OpenADRClient:
    """Create an OpenADR client configured for Business Logic operations."""
    return OpenADRClient(
        base_url=base_url,
        token=token,
        spec_path=spec_path,
        client_type="bl",
        scopes=BL_SCOPES,
        validate=validate,
    )
