# Clojure ↔ Python Comparison

python-oa3 is a port of [clj-oa3](https://github.com/grid-coordination/clj-oa3), the Clojure OpenADR 3 entity library. Both libraries implement the same two-layer data model, entity dispatch, and raw preservation patterns. This document maps the concepts and stack choices between the two.

## Stack Mapping

| Clojure (clj-oa3) | Python (python-oa3) | Role |
|-------------------|---------------------|------|
| Martian + Hato | httpx + openapi-core | Spec-driven HTTP |
| Malli schemas | Pydantic v2 models | Schema validation |
| Tick | Pendulum | DateTime, Duration, interval algebra |
| `camel-snake-kebab` | Pydantic `alias` + `_ID_FIXUPS` dict | Key transformation |
| Multimethods | Dict registry + `coerce()` | Entity dispatch |
| `with-meta {:openadr/raw raw}` | `PrivateAttr(_raw)` | Raw metadata preservation |

## Data Model Mapping

### Namespace Conventions

Clojure uses namespaced keywords; Python uses prefixed snake_case attributes:

| Clojure | Python | Example Value |
|---------|--------|---------------|
| `:openadr/id` | `.id` | `"prog-001"` |
| `:openadr/created` | `.created` | `DateTime(2024, 6, 15, ...)` |
| `:openadr/modified` | `.modified` | `DateTime(2024, 6, 15, ...)` |
| `:openadr/object-type` | `.object_type` | `"PROGRAM"` |
| `:openadr.program/name` | `.program_name` | `"My DR Program"` |
| `:openadr.event/program-id` | `.program_id` | `"prog-001"` |
| `:openadr.ven/name` | `.ven_name` | `"Test VEN"` |
| `:openadr.resource/ven-id` | `.ven_id` | `"ven-001"` |
| `:openadr.report/event-id` | `.event_id` | `"evt-001"` |
| `:openadr.subscription/client-name` | `.client_name` | `"test-client"` |
| `:openadr.interval-period/start` | `.start` | `DateTime(...)` |
| `:openadr.payload/type` | `.type` | `"price"` |

### Raw Preservation

| Clojure | Python |
|---------|--------|
| `(meta entity)` → `{:openadr/raw {...}}` | `entity._raw` → `{...}` |
| Clojure metadata (invisible to equality) | Pydantic PrivateAttr (excluded from serialization) |

### Entity Dispatch

| Clojure | Python |
|---------|--------|
| `(defmulti coerce :objectType)` | `_COERCE_REGISTRY = {"PROGRAM": Program, ...}` |
| `(defmethod coerce "PROGRAM" [raw] (->program raw))` | `coerce(raw)` dispatches via dict lookup |
| `(defmulti coerce-payload :type)` | `_PAYLOAD_REGISTRY = {"PRICE": _coerce_price, ...}` |

Both handle request variants (`BL_VEN_REQUEST`, `VEN_VEN_REQUEST`, etc.) by mapping them to their base entity coercer.

### Key Transformation

The `*ID` suffix is irregular in OpenADR (e.g. `programID` not `programId`):

| Clojure | Python |
|---------|--------|
| `camel-snake-kebab` + manual fixups in notification coercion | `_ID_FIXUPS` dict: `{"program_id": "programID", ...}` |

### Type Coercions

| Field Type | Clojure | Python |
|-----------|---------|--------|
| DateTime | `java.time.Instant` | `pendulum.DateTime` |
| Duration | `java.time.Duration` | `pendulum.Duration` |
| Period/Interval | `tick/interval` (Instant pair) | `tuple[DateTime, DateTime]` |
| PRICE/USAGE values | `BigDecimal` | `decimal.Decimal` |
| Payload type string | Kebab-case keyword (`:openadr.payload-type/price`) | Lowercased string (`"price"`) |
| Object type | Kebab-case keyword (`:openadr.object-type/program`) | Original string (`"PROGRAM"`) |

## API Client Mapping

### Client Creation

```clojure
;; Clojure
(def client (api/create-ven-client "openadr3.yaml" token url))
(api/client-type client)  ;; => :ven
(api/scopes client)       ;; => #{:read_all :read_targets ...}
```

```python
# Python
client = openadr3.create_ven_client(base_url=url, token=token, spec_path="openadr3.yaml")
client.client_type  # => "ven"
client.scopes       # => frozenset({"read_all", "read_targets", ...})
```

### CRUD Operations

```clojure
;; Clojure — raw
(api/get-programs client)              ;; => {:status 200 :body [...]}
(api/get-program-by-id client "p1")    ;; => {:status 200 :body {...}}

;; Clojure — coerced
(api/programs client)                  ;; => [{:openadr/id "p1" ...}]
(api/program client "p1")             ;; => {:openadr/id "p1" ...}
```

```python
# Python — raw
client.get_programs()              # => httpx.Response
client.get_program_by_id("p1")     # => httpx.Response

# Python — coerced
client.programs()                  # => [Program(...)]
client.program("p1")               # => Program(...)
```

### Interceptors vs Auth Hooks

| Clojure | Python |
|---------|--------|
| Martian interceptors | `httpx.Auth` subclass (`BearerAuth`) |
| `create-authentication-header` interceptor | `BearerAuth(token)` passed to `httpx.Client` |
| `turn-off-exception-throwing` interceptor | httpx doesn't throw by default; raw methods return Response |

## Notification Handling

```clojure
;; Clojure
(entities/notification? mqtt-msg)           ;; => true/false
(entities/coerce-notification mqtt-msg)     ;; => {:openadr.notification/object-type :event ...}
```

```python
# Python
openadr3.is_notification(mqtt_msg)          # => True/False
openadr3.coerce_notification(mqtt_msg)      # => Notification(object_type="EVENT", ...)
```

Both convert snake_case MQTT keys to camelCase before coercing the inner object.

## What's Different

| Aspect | Clojure | Python |
|--------|---------|--------|
| Schema layer | Malli schemas separate from data | Pydantic models are both schema and data |
| Validation | `validate-raw-*` functions return explanations | Pydantic raises `ValidationError` |
| Raw models | Malli schemas only (no runtime objects) | `RawBase` Pydantic models with `populate_by_name` |
| Extensibility | `defmethod` on multimethod | Add to `_PAYLOAD_REGISTRY` / `_COERCE_REGISTRY` dicts |
| REPL workflow | Inline via nREPL | Import + call in Python REPL |

## Reference Files

| Python | Clojure Equivalent |
|--------|-------------------|
| `src/openadr3/entities/models.py` | `src/openadr3/entities/schema.clj` |
| `src/openadr3/entities/raw.py` | `src/openadr3/entities/schema/raw.clj` |
| `src/openadr3/entities/__init__.py` | `src/openadr3/entities.clj` |
| `src/openadr3/api.py` | `src/openadr3/api.clj` |
| `src/openadr3/time.py` | `parse-instant`, `parse-duration` in `entities.clj` |
