# OpenTelemetry traces and metrics for replayt workflow runs

## Overview

This project builds on **[replayt](https://pypi.org/project/replayt/)**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for ecosystem positioning, then
**[docs/MISSION.md](docs/MISSION.md)** for scope, audiences, and success criteria.

**Implementation status:** The package currently ships **workflow run tracing** only. OpenTelemetry **metrics** stay on the roadmap and match the mission’s “traces and/or metrics” scope once replayt lifecycle APIs are pinned and declared in the README.

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

CI runs the same checks on Python 3.11 and 3.12 (see `.github/workflows/ci.yml`).

## Enable tracing in development

1. Install runtime dependencies (included in the default package) and, for OTLP HTTP export, the optional extra:

   ```bash
   pip install -e ".[dev,otlp]"
   ```

2. Wire a tracer provider and exporter, then use `workflow_run_span` around a workflow run (or call it from replayt hooks when those are integrated):

   ```python
   from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

   from replayt_opentelemetry_exporter import (
       install_tracer_provider,
       get_workflow_tracer,
       workflow_run_span,
   )

   install_tracer_provider(span_exporters=[OTLPSpanExporter()])
   tracer = get_workflow_tracer()
   with workflow_run_span(tracer, "my-workflow-id", run_id="optional-run-id"):
       ...  # replayt run body
   ```

3. Point `OTEL_EXPORTER_OTLP_ENDPOINT` at your collector (for example Jaeger’s OTLP endpoint) and confirm spans named `replayt.workflow.run` with attributes `replayt.workflow.id` / `replayt.run.id` appear in your backend.

For tests or custom wiring without touching the global provider, use `build_tracer_provider` and obtain a tracer via `provider.get_tracer(...)`.

## Security considerations

- **Transport and endpoints** — In production, point OTLP at an **HTTPS** collector URL (for example via `OTEL_EXPORTER_OTLP_ENDPOINT`). Plain HTTP is only appropriate on trusted local networks. Follow your OpenTelemetry distro’s docs for TLS, mTLS, and proxies.
- **Credentials** — Prefer **environment variables** (for example `OTEL_EXPORTER_OTLP_HEADERS`) or your platform’s secret injection for exporter auth. Do not embed API keys or tokens in source code or commit them to the repository.
- **Data in spans** — Values passed to `workflow_run_span` (`workflow_id`, `run_id`) and to `build_resource` (`extra_attributes`) are **exported to your observability backend** and may appear in vendor UIs, support tickets, and long-term retention stores. Do not put secrets, raw credentials, or unnecessary personally identifiable information (PII) in span or resource attributes. Treat them like structured logs from a confidentiality perspective.
- **Supply chain** — Keep OpenTelemetry and this package **updated** in line with your organization’s patch policy; pinned ranges in `pyproject.toml` should be reviewed when cutting releases.

## Optional agent workflows

This repo may include a [`.cursor/skills/`](.cursor/skills/) directory for Cursor-style agent skills. **`.gitignore`**
lists **`.cursor/skills/`** so those files stay local and are not pushed. Adapt or remove the directory to match your
team’s tooling.

## Project layout

| Path | Purpose |
| ---- | ------- |
| `docs/REPLAYT_ECOSYSTEM_IDEA.md` | Positioning (core-gap / showcase / bridge / combinator prompts) |
| `docs/MISSION.md` | Mission and scope |
| `docs/DESIGN_PRINCIPLES.md` | Design and integration principles |
| `docs/reference-documentation/` | Optional markdown snapshot for contributors (when present) |
| `src/replayt_opentelemetry_exporter/` | Python package (import `replayt_opentelemetry_exporter`) |
| `tests/` | Pytest suite |
| `pyproject.toml` | Package metadata, Ruff and pytest settings |
| `.github/workflows/ci.yml` | Lint and test workflow |
| `.gitignore` | Ignores `.orchestrator/` and `.cursor/skills/` (local tooling) |
