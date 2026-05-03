# Contributing to python-oa3

Thanks for your interest in contributing! This repo is a Python client library for the [OpenADR 3](https://www.openadr.org/) API. It is built against the [OpenADR 3.1.0 specification](resources/openadr3.yaml) (Apache 2.0; see [`resources/ORIGIN.md`](resources/ORIGIN.md) for provenance) and exposes a two-layer raw/coerced data model with Pydantic v2 schemas, pendulum time types, and an httpx-based client.

## How to contribute

### Discussions

Use [Discussions](https://github.com/grid-coordination/python-oa3/discussions) for:

- Questions about how to use the library — clients, coercion, raw/coerced layering, time handling, payload dispatch
- API and design judgment calls — "should python-oa3 model X?" / "is this the right shape for Y?"
- OpenADR spec or VTN behavior gaps that affect python-oa3 — when a VTN exposes something that doesn't fit the current entity shape and you want to scope what the library should do about it
- Coordination with the upstream [OpenADR 3.1.0 specification](resources/openadr3.yaml) and the [VTN Reference Implementation](https://github.com/oadr3-org/openadr3-vtn-reference-implementation) (whose snake_case notification format the library accommodates)
- Sharing what you're building on top of python-oa3

Discussions are open-ended — a good place to think out loud or scope something before it becomes a concrete change. Aligned outcomes from a Discussion often turn into one or more Issues.

### Issues

Use [Issues](https://github.com/grid-coordination/python-oa3/issues) for actionable changes:

- Bugs in client construction, request building, response parsing, or coercion against a real VTN
- Coercion or schema gaps surfaced by real VTN responses (a field the library doesn't handle, or a value that breaks the coerced shape)
- New entity types, new endpoints, or new request parameters when the spec or a VTN exposes them
- Test failures or unexpected behavior with concrete repro steps
- Documentation errors, unclear explanations, or stale prose in `README.md` or docstrings
- Discussion outcomes that have alignment and a clear scope

If you're not sure whether something is an Issue or a Discussion, start with a Discussion — we can convert it later.

### Pull requests

Pull requests are welcome.

- For small fixes (typos, broken links, single-test corrections, single-coercion bug fixes), open a PR directly.
- For substantive changes (new entity types, new endpoints, new schema fields, new payload dispatch behavior, new modules), open a Discussion or Issue first so we can align on scope before you invest the effort.
- All changes pass `pytest tests/` and `ruff check src/` / `ruff format --check src/` cleanly. CI runs the test suite across Python 3.10–3.13.
- Match the existing tone and structure. The library composes spec-driven HTTP → raw Pydantic models → coerced entities as roughly orthogonal layers; patches that fit cleanly into one layer without leaking concerns across them are the easiest to land.
- One commit per logical change is fine; we don't require squash or any particular branch naming.

## Development

```bash
pip install -e ".[dev]"           # install with dev dependencies
pytest tests/ -v                  # run the unit test suite (offline)
ruff check src/                   # lint
ruff format --check src/          # format check (drop --check to apply)
mypy src/openadr3/                # type check (py.typed marker included)
```

### Pre-commit hooks

This project uses [pre-commit](https://pre-commit.com/) to run Ruff lint and format checks automatically:

```bash
pip install pre-commit
pre-commit install
```

Ruff lint + format are also enforced in CI via `.github/workflows/ci.yml`.

### OpenAPI spec

The OpenADR 3.1.0 specification under `resources/openadr3.yaml` is vendored from the OpenADR Alliance and serves as the single source of truth for routes, parameters, and request/response shapes — see [`resources/ORIGIN.md`](resources/ORIGIN.md) for provenance. When the upstream spec changes, re-vendor the file and re-run the test suite to confirm raw/coerced models still line up with the wire format.

## Code of conduct

Be respectful and constructive. We're a small project and appreciate everyone who takes the time to file an issue or send a PR.

## Important notice

This library is provided on an "as-is" basis. Updates and maintenance, including responses to issues filed on GitHub, will take place on an "as time and resources permit" basis. Library output (raw API responses, coerced entities, payload values) is best-effort against the [OpenADR 3.1.0 specification](resources/openadr3.yaml) and the behavior of real-world VTN implementations (including the [VTN Reference Implementation](https://github.com/oadr3-org/openadr3-vtn-reference-implementation)). This library is not authoritative for billing, dispatch, or grid operations — independent verification against the source spec and your VTN's actual responses is recommended for any consumer relying on these results for operational correctness.
