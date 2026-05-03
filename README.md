# python-oa3

[![PyPI version](https://img.shields.io/pypi/v/openadr3.svg)](https://pypi.org/project/openadr3/)
[![Python versions](https://img.shields.io/pypi/pyversions/openadr3.svg)](https://pypi.org/project/openadr3/)
[![CI](https://github.com/grid-coordination/python-oa3/actions/workflows/ci.yml/badge.svg)](https://github.com/grid-coordination/python-oa3/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python client library for the [OpenADR 3](https://www.openadr.org/) API. Provides Pydantic v2 models with a two-layer coercion pattern (raw JSON shape + snake_case typed entities), an httpx-based API client, and pendulum-powered time types.

## Installation

```bash
pip install -e ".[dev]"
```

### Dependencies

| Package | Role |
|---------|------|
| [Pydantic](https://docs.pydantic.dev/) v2 | Schema validation, model coercion |
| [Pendulum](https://pendulum.eustace.io/) v3 | DateTime, Duration, timezone handling |
| [httpx](https://www.python-httpx.org/) | HTTP client with auth hooks |
| [openapi-core](https://openapi-core.readthedocs.io/) | Optional OpenAPI spec validation |
| [PyYAML](https://pyyaml.org/) | OpenAPI spec loading |

## Architecture

### Two-Layer Data Model

Every OpenADR 3 entity exists in two forms:

1. **Raw models** (`openadr3.entities.raw`) — Mirror the JSON API shape exactly. CamelCase field aliases, string datetimes, string durations. Useful for serialization and wire-format validation.

2. **Coerced models** (`openadr3.entities.models`) — Snake_case fields, `pendulum.DateTime` for timestamps, `pendulum.Duration` for durations, `Decimal` for PRICE/USAGE payloads. These are what you work with in application code.

```
JSON API response (camelCase, strings)
  │
  ▼
coerce(raw_dict)  ──►  Typed entity (snake_case, pendulum, Decimal)
                            │
                            └─► ._raw  (original dict preserved)
```

### Raw Preservation

Every coerced entity carries its original raw dict as a Pydantic `PrivateAttr`:

```python
program = openadr3.coerce(api_response)
program.program_name        # "My DR Program"
program.created             # DateTime(2024, 6, 15, 10, 0, 0, tzinfo=UTC)
program._raw["programName"] # "My DR Program" (original wire format)
```

### Entity Dispatch

The `coerce()` function dispatches on the `objectType` string in the raw dict:

```python
from openadr3 import coerce

raw = {"objectType": "PROGRAM", "programName": "Test", ...}
program = coerce(raw)  # Returns a Program instance

raw = {"objectType": "EVENT", "programID": "p1", ...}
event = coerce(raw)    # Returns an Event instance
```

Handles request variants too: `BL_VEN_REQUEST` and `VEN_VEN_REQUEST` coerce as `Ven`, `BL_RESOURCE_REQUEST` and `VEN_RESOURCE_REQUEST` coerce as `Resource`.

### Notification Coercion

`coerce_notification()` handles both spec-compliant camelCase notifications and the snake_case format currently sent by the VTN Reference Implementation:

```python
from openadr3 import coerce_notification, is_notification

# Spec-compliant (camelCase)
webhook_payload = {
    "objectType": "EVENT",
    "operation": "CREATE",
    "object": {"programID": "prog-001", "eventName": "Peak Event", ...}
}

# VTN-RI (snake_case) — see oadr3-org/openadr3-vtn-reference-implementation#181
mqtt_payload = {
    "object_type": "EVENT",
    "operation": "CREATE",
    "object": {"program_id": "prog-001", "event_name": "Peak Event", ...}
}

# Both formats work
for payload in [webhook_payload, mqtt_payload]:
    if is_notification(payload):
        notification = coerce_notification(payload)
        notification.object  # Coerced Event instance
```

## Entity Types

| Entity | Key Fields | Notes |
|--------|-----------|-------|
| `Program` | `program_name`, `interval_period`, `descriptions`, `payload_descriptors`, `attributes`, `targets` | Top-level DR program |
| `Event` | `program_id`, `event_name`, `duration`, `priority`, `intervals`, `targets` | DR event with signal intervals |
| `Ven` | `ven_name`, `client_id`, `attributes`, `targets` | Virtual End Node |
| `Resource` | `resource_name`, `ven_id`, `client_id`, `attributes`, `targets` | Device/load under a VEN |
| `Report` | `event_id`, `client_name`, `resources` | VEN telemetry report |
| `Subscription` | `client_name`, `object_operations`, `program_id`, `targets` | Webhook/MQTT subscription |
| `Notification` | `object_type`, `operation`, `object` | Push notification wrapper |

All top-level entities share common metadata: `id`, `created` (DateTime), `modified` (DateTime), `object_type`.

### Supporting Types

| Type | Description |
|------|-------------|
| `IntervalPeriod` | Start datetime + duration + computed period tuple |
| `Interval` | Numbered interval with payloads |
| `Payload` | Type-tagged values (PRICE/USAGE get Decimal coercion) |
| `EventPayloadDescriptor` | Event payload descriptor (payloadType, units, currency) |
| `ReportPayloadDescriptor` | Report payload descriptor (payloadType, readingType, units, accuracy, confidence) |
| `ObjectOperation` | Subscription callback definition |

## API Client

### Quick Start

```python
import openadr3

# Create a VEN client
client = openadr3.create_ven_client(
    base_url="https://vtn.example.com/openadr3/3.1.0",
    token="your-bearer-token",
    spec_path="resources/openadr3.yaml",  # optional, for route introspection
)

# Coerced entity methods — returns typed models
programs = client.programs()
event = client.event("evt-001")
print(event.program_id)   # "prog-001"
print(event.created)      # DateTime(2024, 6, 15, ...)
print(event._raw)         # Original API dict

# Raw HTTP methods — returns httpx.Response
resp = client.get_events(programID="prog-001")
if openadr3.success(resp):
    data = openadr3.body(resp)
```

### Client Types

```python
# VEN client — scopes: read_all, read_targets, read_ven_objects,
#              write_reports, write_subscriptions, write_vens
ven = openadr3.create_ven_client(base_url, token)

# Business Logic client — scopes: read_all, read_bl,
#              write_programs, write_events, write_subscriptions, write_vens
bl = openadr3.create_bl_client(base_url, token)

# Custom client
client = openadr3.OpenADRClient(
    base_url="https://vtn.example.com/openadr3/3.1.0",
    token="tok",
    spec_path="resources/openadr3.yaml",
    client_type="custom",
    scopes=frozenset({"read_all", "write_events"}),
)
```

### Available Methods

**Coerced** (return entity models):

| Method | Returns |
|--------|---------|
| `client.programs()` | `list[Program]` |
| `client.program(id)` | `Program` |
| `client.events()` | `list[Event]` |
| `client.event(id)` | `Event` |
| `client.vens()` | `list[Ven]` |
| `client.ven(id)` | `Ven` |
| `client.resources()` | `list[Resource]` |
| `client.resource(id)` | `Resource` |
| `client.reports()` | `list[Report]` |
| `client.report(id)` | `Report` |
| `client.subscriptions()` | `list[Subscription]` |
| `client.subscription(id)` | `Subscription` |
| `client.find_program_by_name(name)` | `Program \| None` |
| `client.find_ven_by_name(name)` | `Ven \| None` |

**Raw** (return `httpx.Response`):

Each entity has: `get_<entities>()`, `get_<entity>_by_id(id)`, `create_<entity>(data)`, `update_<entity>(id, data)`, `delete_<entity>(id)`.

**Introspection** (requires `spec_path`):

```python
client.all_routes()                        # ["/programs", "/programs/{programID}", ...]
client.endpoint_scopes("/programs", "get") # ["read_all"]
client.authorized("/events", "post")       # True/False based on client scopes
```

### User-Agent

Every client sends a `User-Agent` header for server-side log identification. The default is `openadr3/<version> (node=<hex>)` where the node ID comes from `uuid.getnode()` (MAC-derived, stable across restarts).

Override it to identify your application:

```python
client = openadr3.create_ven_client(
    base_url=base_url,
    token=token,
    user_agent="my-ven-app/1.0",
)

# Or compose a layered string with the default
from openadr3.api import DEFAULT_USER_AGENT
client = openadr3.OpenADRClient(
    base_url=base_url,
    user_agent=f"my-app/1.0 {DEFAULT_USER_AGENT}",
)
```

The User-Agent is preserved across `fetch_token()` client recreation.

### Context Manager

```python
with openadr3.create_ven_client(base_url, token) as client:
    programs = client.programs()
```

## Authentication

```python
from openadr3 import BearerAuth, fetch_token

# Fetch an OAuth2 token
token = fetch_token(
    base_url="https://vtn.example.com/openadr3/3.1.0",
    client_id="my-client",
    client_secret="secret",
    scopes=["read_all", "write_reports"],
)

# Use BearerAuth directly with httpx
auth = BearerAuth(token)
```

## Time and Timezones

Datetimes are zone-aware end-to-end. The library treats the **wire string's offset as the source of truth** and preserves it through parse → serialize without normalization.

| Wire string | Round-trip output | Notes |
|-------------|-------------------|-------|
| `2024-06-15T10:30:00Z` | `2024-06-15T10:30:00Z` | UTC literal preserved |
| `2024-06-15T10:30:00+00:00` | `2024-06-15T10:30:00+00:00` | **Not** normalized to `Z` |
| `2024-06-15T10:30:00-07:00` | `2024-06-15T10:30:00-07:00` | Negative offsets preserved |
| `2024-06-15T10:30:00+05:30` | `2024-06-15T10:30:00+05:30` | Half-hour offsets preserved |
| `2024-06-15T10:30:00.123456Z` | `2024-06-15T10:30:00.123456Z` | Sub-second precision preserved |

This holds at both the `parse_datetime` / `.to_iso8601_string()` level and end-to-end through Pydantic models that use the `PendulumDateTime` annotated type. Round-trip behavior is covered by the test suite (`tests/test_time.py::TestWireOffsetPreservation`, `TestPydanticAnnotatedRoundTrip`).

### Parsing and conversion

```python
from openadr3 import parse_datetime, parse_duration, to_zoned

# Parse datetimes (handles VTN-RI non-standard formats)
dt = parse_datetime("2024-06-15T14:00:00Z")
dt = parse_datetime("2024-06-15 14:00:00Z")  # space instead of T

# Parse ISO 8601 durations
dur = parse_duration("PT2H30M")

# Convert to a named timezone (returns a new pendulum.DateTime)
eastern = to_zoned(dt, "America/New_York")
```

`to_zoned` is the only operation that intentionally changes the wire offset — it's an explicit conversion, not a normalization on parse.

### Pydantic Annotated Types

`PendulumDateTime` and `PendulumDuration` are `Annotated` types with `BeforeValidator` and `PlainSerializer`, ready for use in your own Pydantic models. Pendulum types require `arbitrary_types_allowed=True` in the model config:

```python
from pydantic import BaseModel, ConfigDict
from openadr3 import PendulumDateTime, PendulumDuration

class MyModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    start: PendulumDateTime = None
    length: PendulumDuration = None
```

## Enums

```python
from openadr3 import ObjectType, Operation, PayloadType

ObjectType.PROGRAM   # "PROGRAM"
Operation.CREATE     # "CREATE"
PayloadType.PRICE    # "PRICE"
```

## Payload Coercion

Payload values are dispatched by type string:

| Payload Type | Coercion |
|-------------|----------|
| `PRICE` | Values become `Decimal`, type becomes `"price"` |
| `USAGE` | Values become `Decimal`, type becomes `"usage"` |
| All others | Values pass through, type lowercased |

The registry is extensible — add entries to `openadr3.entities.payloads._PAYLOAD_REGISTRY`.

## Module Structure

```
src/openadr3/
├── __init__.py          # Public API re-exports
├── py.typed             # PEP 561 type stub marker
├── time.py              # Pendulum parsing, annotated types
├── enums.py             # ObjectType, Operation, PayloadType
├── auth.py              # BearerAuth, OAuth2 token fetch
├── api.py               # OpenADRClient, create_ven_client, create_bl_client
└── entities/
    ├── __init__.py      # coerce(), coerce_notification(), is_notification()
    ├── models.py        # Coerced Pydantic models (snake_case, pendulum)
    ├── raw.py           # Raw Pydantic models (camelCase, strings)
    └── payloads.py      # Payload type dispatch (PRICE/USAGE → Decimal)
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint and format
ruff check src/
ruff format --check src/

# Type check (py.typed marker included)
mypy src/openadr3/
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to run Ruff lint and format checks automatically:

```bash
pip install pre-commit
pre-commit install
```

Ruff lint + format are also enforced in CI via `.github/workflows/ci.yml`.

## OpenAPI Spec

The OpenADR 3.1.0 specification is embedded at `resources/openadr3.yaml`. See `resources/ORIGIN.md` for provenance and license.

## Contributing

Issues, Discussions, and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow (and the dev commands: tests, lint, format, type check, pre-commit). In short:

- **Questions, API/design discussion, OpenADR spec or VTN behavior gaps** → [Discussions](https://github.com/grid-coordination/python-oa3/discussions)
- **Confirmed bugs, coercion/schema fixes, doc errors** → [Issues](https://github.com/grid-coordination/python-oa3/issues)
- **Patches** → pull requests; please open a Discussion or Issue first for non-trivial changes (new entity types, new endpoints, new schema fields, new payload dispatch behavior)

## License

[MIT License](LICENSE) — Copyright (c) 2026 Clark Communications Corporation
