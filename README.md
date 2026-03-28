# OpenTelemetry traces and metrics for replayt workflow runs

## Overview

This project builds on **[replayt](https://pypi.org/project/replayt/)**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for ecosystem positioning, then
**[docs/MISSION.md](docs/MISSION.md)** for scope, audiences, and success criteria.

**Implementation status:** The package targets **workflow run tracing** and **metrics** for run outcomes and exporter health. The **canonical contract** for symbols, run boundaries, and metric names is **[docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md)** (spec for integrators and Builder).

## Public API (summary)

- **Specification:** [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) — stable exports (`__all__`), replayt integration seam, run-boundary semantics, OTel metric names, version expectations, and testable acceptance criteria.
- **Quick pattern:** install global tracer and meter providers, obtain a tracer via `get_workflow_tracer()`, wrap each logical run with `workflow_run_span(...)`. See the example in **Enable tracing and metrics in development** below.

### Public surface at a glance

These symbols are the intended stable exports (see the spec for parameters and semantics):

| Area | Symbols |
| ---- | ------- |
| Version | `__version__` |
| Resource / providers | `build_resource`, `build_tracer_provider`, `build_meter_provider`, `install_tracer_provider`, `install_meter_provider` |
| Run boundary | `get_workflow_tracer`, `workflow_run_span` |
| Run summary | `RunSummary`, `generate_run_summary` |
| Advanced metrics | `record_run_outcome`, `record_exporter_error` |

## Version compatibility

Declared dependency ranges live in **`pyproject.toml`**. At a high level:

- **Python:** `>=3.11` (`requires-python`).
- **OpenTelemetry:** `opentelemetry-api` and `opentelemetry-sdk` `>=1.20.0`.
- **replayt:** `>=0.1.0` (upper bound **TODO** until a breaking replayt release is validated here).

CI installs the latest **replayt** matching `>=0.1.0` from PyPI (see the workflow log line `replayt <version>`). Mission Control baseline logs used **0.4.25** as the public API snapshot for examples until you pin otherwise—see [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §7.

## Design principles

**[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** covers **replayt** compatibility, versioning, and (for showcases)
**LLM** boundaries.


## Reference documentation (optional)

This checkout does not yet include [`docs/reference-documentation/`](docs/reference-documentation/). You can add markdown
copies of upstream replayt documentation there for offline review or agent context.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
```

## Running tests and lint locally

From the repository root after a dev install:

```bash
pytest
python -m ruff check .
python -m ruff format --check .
```

CI runs the same checks on Python 3.12 (see `.github/workflows/ci.yml`). Each workflow run logs the resolved **replayt** wheel version after install.

## Enable tracing and metrics in development

1. Install runtime dependencies (included in the default package) and, for OTLP HTTP export, the optional extra:

   ```bash
   pip install -e ".[dev,otlp]"
   ```

2. Wire a tracer provider and exporter, then use `workflow_run_span` around the integrator-owned block that runs a workflow (for example the code that calls replayt’s `Runner` / `Workflow` / `run_with_mock`). See **§2** and **§3** of [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) for the integration seam and full `__all__` list.

   ```python
   from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
   from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

   from replayt_opentelemetry_exporter import (
       install_tracer_provider,
       install_meter_provider,
       get_workflow_tracer,
       workflow_run_span,
   )

   # Install both tracer and meter providers
   install_tracer_provider(span_exporters=[OTLPSpanExporter()])
   install_meter_provider(metric_exporters=[OTLPMetricExporter()])

   tracer = get_workflow_tracer()
   with workflow_run_span(tracer, "my-workflow-id", run_id="optional-run-id"):
       ...  # e.g. replayt Runner / Workflow invocation
   ```

3. Point `OTEL_EXPORTER_OTLP_ENDPOINT` at your collector (for example Jaeger's OTLP endpoint) and confirm spans named `replayt.workflow.run` with attributes `replayt.workflow.id` / `replayt.run.id` appear in your backend. Verify span **events** `replayt.workflow.run.started` and `replayt.workflow.run.completed` and completion attributes such as `replayt.workflow.outcome` (and on failures `replayt.workflow.error.type` / `replayt.workflow.failure.category`) so operators can see run start and outcome without reading raw exception messages in attributes. Names and semantics are defined in [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§6**.

For tests or custom wiring without touching the global provider, use `build_tracer_provider` and `build_meter_provider` and obtain a tracer/meter via `provider.get_tracer(...)` or `provider.get_meter(...)`. For in-process metric assertions, pass `metric_readers=[InMemoryMetricReader()]` to `build_meter_provider`; OTLP and similar backends keep using `metric_exporters`.

## Metrics

Canonical **instrument names**, types, and semantics are defined in **[docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §5** (and tracked under **Unreleased** in [CHANGELOG.md](CHANGELOG.md)). Summary:

| Instrument | Name (canonical) |
| ---------- | ---------------- |
| Counter | `replayt.workflow.run.outcomes_total` (e.g. `outcome` attribute) |
| Histogram | `replayt.workflow.run.duration_ms` |
| Counter | `replayt.exporter.errors_total` |

### Metric attributes and cardinality

| Instrument | Attributes (string keys) |
| ---------- | ------------------------ |
| `replayt.workflow.run.outcomes_total` | `outcome` (`success` / `failure`), `workflow_id`; optional `run_id` when the integrator supplies one |
| `replayt.workflow.run.duration_ms` | `outcome`, `workflow_id`; optional `run_id` |
| `replayt.exporter.errors_total` | `error_type`; optional `workflow_id`, `run_id` |

`error_type` SHOULD be one of `export_failed`, `serialization_error`, `timeout`, or `unknown` (see [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §5.3). Other strings are recorded as `unknown`.

- Prefer stable **workflow** and **run** identifiers that are safe to emit.
- Keep labels **low-cardinality**; do not put unbounded or secret-bearing values on metrics. See [docs/SECURITY_REDACTION.md](docs/SECURITY_REDACTION.md).

## Security considerations

- **Transport and endpoints** — In production, point OTLP at an **HTTPS** collector URL (for example via `OTEL_EXPORTER_OTLP_ENDPOINT`). Plain HTTP is only appropriate on trusted local networks. Follow your OpenTelemetry distro's docs for TLS, mTLS, and proxies.
- **Credentials** — Prefer **environment variables** (for example `OTEL_EXPORTER_OTLP_HEADERS`) or your platform's secret injection for exporter auth. Do not embed API keys or tokens in source code or commit them to the repository.
- **Data in spans and metrics** — Values passed to `workflow_run_span` (`workflow_id`, `run_id`, optional extra attributes) and to `build_resource` (`extra_attributes`) are **exported to your observability backend** and may appear in vendor UIs, support tickets, and long-term retention stores. Do not put secrets, raw credentials, or unnecessary personally identifiable information (PII) in span or resource attributes. Treat them like structured logs from a confidentiality perspective.
- **Supply chain** — Keep OpenTelemetry and this package **updated** in line with your organization's patch policy; pinned ranges in `pyproject.toml` should be reviewed when cutting releases.

## Optional agent workflows

This repo may include a [`.cursor/skills/`](.cursor/skills/) directory for Cursor-style agent skills. **`.gitignore`**
lists **`.cursor/skills/`** so those files stay local and are not pushed. Adapt or remove the directory to match your
team's tooling.

## Project layout

| Path | Purpose |
| ---- | ------- |
| `docs/REPLAYT_ECOSYSTEM_IDEA.md` | Positioning (core-gap / showcase / bridge / combinator prompts) |
| `docs/MISSION.md` | Mission and scope |
| `docs/DESIGN_PRINCIPLES.md` | Design and integration principles |
| `docs/PUBLIC_API_SPEC.md` | Public API, replayt seam, run boundaries, metric names, versions |
| `docs/reference-documentation/` | Optional markdown snapshot for contributors (when present) |
| `src/replayt_opentelemetry_exporter/` | Python package (import `replayt_opentelemetry_exporter`) |
| `tests/` | Pytest suite |
| `pyproject.toml` | Package metadata, Ruff and pytest settings |
| `.github/workflows/ci.yml` | Lint and test workflow |
| `.gitignore` | Ignores `.orchestrator/` and `.cursor/skills/` (local tooling) |
