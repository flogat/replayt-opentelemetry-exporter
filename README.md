# OpenTelemetry traces and metrics for replayt workflow runs

## Overview

This project builds on **[replayt](https://pypi.org/project/replayt/)**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for ecosystem positioning, then
**[docs/MISSION.md](docs/MISSION.md)** for scope, audiences, and success criteria.

**Implementation status:** The package targets **workflow run tracing** and **metrics** for run outcomes and exporter health. The **canonical contract** for symbols, run boundaries, and metric names is **[docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md)** (spec for integrators and Builder).

## Public API (summary)

- **Specification:** [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) — stable exports (`__all__`), replayt integration seam, run-boundary semantics, OTel metric names, version expectations, and testable acceptance criteria.
- **Testing contract:** [docs/TESTING_SPEC.md](docs/TESTING_SPEC.md) — pytest commands, success/failure/exporter-error scenarios, in-memory fakes, replayt public-surface-only rule, and CI parity.
- **CI contract:** [docs/CI_SPEC.md](docs/CI_SPEC.md) — Ruff + pytest step naming, exit codes, and log hygiene (matches [DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md) **Observable automation**).
- **Releases:** [docs/RELEASE_ENGINEERING_SPEC.md](docs/RELEASE_ENGINEERING_SPEC.md) — maintainer checklist (**§4**), strategy **B** version sync (**§6.1**), [`.github/workflows/publish-pypi.yml`](.github/workflows/publish-pypi.yml) for tag-gated **OIDC** publish (**§5.2**).
- **Quick pattern:** install global tracer and meter providers, obtain a tracer via `get_workflow_tracer()`, wrap each logical run with `workflow_run_span(...)`. See **Enable tracing and metrics in development** below. For a **`Runner.run`** walk-through with **`MockLLMClient`**, see [docs/examples/runner_workflow_run_span.md](docs/examples/runner_workflow_run_span.md).

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

**Normative policy** (matrix shape, justified pins, how CI should validate): **[docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md)**. That spec maps the backlog *Add compatibility matrix and dependency pins for replayt and OpenTelemetry* to testable Builder obligations. This package stays on **OpenTelemetry 1.x** within the declared range (`pyproject.toml` caps API/SDK **below 2**). A **2026-03-29** PyPI audit found **no** published **2.x** API/SDK (see that document **§7.2**). Spike workflow, documentation outcomes, and when CI may add **2.x** matrix cells are in **§7**, with integrator policy in **[docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §7.4**.

Declared dependency ranges live in **`pyproject.toml`**. Current snapshot:

| Component | Supported range (see `pyproject.toml`) | CI / validation |
| --------- | -------------------------------------- | ---------------- |
| Python | `>=3.11` (`requires-python`) | **3.12:** job **`test`**, full replayt×OpenTelemetry matrix (merge gate). **3.11:** job **`test-python-3-11`** in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (`schedule` + `workflow_dispatch` only; same Ruff/pytest commands)—[docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§4.3**, [docs/CI_SPEC.md](docs/CI_SPEC.md) **§3.6**. |
| OpenTelemetry API / SDK | `>=1.20.0,<2` each | `test` **strategy.matrix**: pins **1.20.0** and **1.40.0** (each cell reinstalls API + SDK to the same version); **Print resolved dependency versions** logs `replayt`, `opentelemetry-api`, `opentelemetry-sdk` |
| replayt | `>=0.4.0` (no upper cap yet—see [COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§3**) | Same matrix: **0.4.0** and PyPI **latest** (`pip install --upgrade --force-reinstall replayt`) |
| OTLP HTTP extra (`[otlp]`) | `opentelemetry-exporter-otlp-proto-http>=1.20.0,<2` | Same OpenTelemetry major as API/SDK; install locally with `pip install -e ".[dev,otlp]"` and match a matrix cell if you need parity |

Matrix updates are validated by that workflow: every push runs **Ruff** and **pytest** once per cell on **3.12**. Job **`test-python-3-11`** runs the same Ruff and pytest commands for one documented pin set (**replayt** latest, OpenTelemetry API/SDK **1.40.0**) on **`schedule`** and **`workflow_dispatch`** only (not on every PR unless branch protection is changed to require it)—see [docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§4.3**. Approximate a cell locally with `pip install "replayt==0.4.0" "opentelemetry-api==1.20.0" "opentelemetry-sdk==1.20.0"` (or `latest` / `1.40.0` as needed), then `pytest` from the repo root after `pip install -e ".[dev]"`.

## Design principles

**[docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md)** covers **replayt** compatibility, versioning, and (for showcases)
**LLM** boundaries.


## Reference documentation

**Contract:** [docs/REFERENCE_DOCUMENTATION_SPEC.md](docs/REFERENCE_DOCUMENTATION_SPEC.md). Bounded, version-stamped
markdown for replayt’s **Workflow**, **Runner**, **RunContext**, and **run_with_mock** lives under
[`docs/reference-documentation/`](docs/reference-documentation/) (index [README](docs/reference-documentation/README.md)),
aligned with the replayt pins in [docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§4.1**. Use
replayt’s PyPI page and installed docstrings for the full upstream story.

**Runner example:** [docs/examples/runner_workflow_run_span.md](docs/examples/runner_workflow_run_span.md) walks through **`Runner.run`** with **`MockLLMClient`** inside **`workflow_run_span`** (PUBLIC_API_SPEC §3.4).

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
python -m ruff check src tests
python -m ruff format --check src tests
```

**Exit codes:** `pytest` exits **`0`** when all tests pass and **non-zero** on failure (standard pytest semantics). Normative test obligations (success vs failure vs exporter-error coverage, fakes, replayt boundary) live in **[docs/TESTING_SPEC.md](docs/TESTING_SPEC.md)**.

**CI entry point:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — job **`test`** runs the Ruff and pytest commands above (after matrix pins) in **separate steps** so the Actions UI shows whether lint, format, or tests failed; see **[docs/CI_SPEC.md](docs/CI_SPEC.md)** for the full contract.

CI runs those checks on Python **3.12** (job **`test`**). Each matrix cell reinstalls pinned **replayt** and OpenTelemetry API/SDK versions, then logs all three distributions before Ruff and pytest. Job **`test-python-3-11`** runs the same steps for **replayt** latest and OpenTelemetry **1.40.0** on Python **3.11** when the workflow is triggered by **`schedule`** or **`workflow_dispatch`** (informational unless you mark it required in branch protection); see [docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§4.3** and [docs/CI_SPEC.md](docs/CI_SPEC.md) **§3.6**.

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

### Operator monitoring (dashboards and alerts)

**[docs/OPERATOR_RUNBOOK.md](docs/OPERATOR_RUNBOOK.md)** — PromQL-style examples, Grafana panel intents, and alert starting points for the §5 metrics, aligned with [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§5–§6** (label semantics and cardinality). Confirm metric and label names on your OTLP → Prometheus (or vendor) pipeline before copying queries verbatim.

Normative checklist and backlog mapping: **[docs/OPERATOR_MONITORING_SPEC.md](docs/OPERATOR_MONITORING_SPEC.md)**.

## Releases and PyPI (maintainers)

**Normative spec:** [docs/RELEASE_ENGINEERING_SPEC.md](docs/RELEASE_ENGINEERING_SPEC.md) — maintainer checklist (**§4**), **`python -m build`** + **`twine check`**, **tag** naming (**§6.2**), **CHANGELOG** cut rules (**§6.3**), and **GitHub Actions** for **OIDC trusted publishing** (**§5.2**). The package name on PyPI is **`replayt-opentelemetry-exporter`** (from **`pyproject.toml`** **`[project].name`**).

**Version (strategy B):** The distribution version is **`[project].version`** in **`pyproject.toml`** only. **`replayt_opentelemetry_exporter.__version__`** reads **`importlib.metadata.version("replayt-opentelemetry-exporter")`** so there is no second literal to drift. **`tests/test_version_sync.py`** enforces equality between **`pyproject.toml`**, installed metadata, and **`__version__`**.

**Local build and check** (after `pip install -e ".[dev]"` so **`build`** and **`twine`** are available):

```bash
python -m build
twine check dist/*
```

**Publish on PyPI:** Workflow [`.github/workflows/publish-pypi.yml`](.github/workflows/publish-pypi.yml) runs on **`vMAJOR.MINOR.PATCH`** tags (for example **`v0.2.0`**). It builds with **`python -m build`** and uploads using **`pypa/gh-action-pypi-publish`** with **OIDC**; the default path does **not** use a long-lived **`PYPI_API_TOKEN`** repository secret. First-time maintainers register the GitHub repo and workflow in the PyPI project’s **trusted publisher** settings; see [PyPI trusted publishers](https://docs.pypi.org/trusted-publishers/).

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
| `docs/COMPATIBILITY_MATRIX_SPEC.md` | Compatibility matrix, dependency pin justification, CI validation policy |
| `docs/TESTING_SPEC.md` | Pytest strategy, replayt boundary and exporter-error test obligations |
| `docs/CI_SPEC.md` | CI step naming, Ruff + pytest commands, exit codes, safe logs |
| `docs/RELEASE_ENGINEERING_SPEC.md` | PyPI publish, version sync, tag-gated trusted publishing, changelog alignment |
| `docs/OPERATOR_MONITORING_SPEC.md` | Operator dashboards/alerts spec for §5 metrics |
| `docs/OPERATOR_RUNBOOK.md` | Operator PromQL/Grafana/alert guidance for canonical metrics |
| `docs/REFERENCE_DOCUMENTATION_SPEC.md` | Spec for bounded replayt public-surface snapshots under `docs/reference-documentation/` |
| `docs/reference-documentation/` | Version-stamped replayt workflow/run API notes (see [README](docs/reference-documentation/README.md)) |
| `src/replayt_opentelemetry_exporter/` | Python package (import `replayt_opentelemetry_exporter`) |
| `tests/` | Pytest suite |
| `pyproject.toml` | Package metadata, Ruff and pytest settings |
| `.github/workflows/ci.yml` | Lint and test workflow |
| `.github/workflows/publish-pypi.yml` | Tag-gated PyPI publish (OIDC trusted publishing) |
| `.gitignore` | Ignores `.orchestrator/` and `.cursor/skills/` (local tooling) |
