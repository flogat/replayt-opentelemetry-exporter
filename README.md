# OpenTelemetry traces and metrics for replayt workflow runs

## Overview

This project builds on **[replayt](https://pypi.org/project/replayt/)**. Read
**[docs/REPLAYT_ECOSYSTEM_IDEA.md](docs/REPLAYT_ECOSYSTEM_IDEA.md)** for ecosystem positioning, then
**[docs/MISSION.md](docs/MISSION.md)** for scope, audiences, and success criteria.

**Implementation status:** The package targets **workflow run tracing** and **metrics** for run outcomes and exporter health. The **canonical contract** for symbols, run boundaries, and metric names is **[docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md)** (spec for integrators and Builder).

## Public API (summary)

- **Specification:** [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) — stable exports (`__all__`), replayt integration seam, run-boundary semantics, OTel metric and trace naming (including **§5.7** and **§6.8** vs OpenTelemetry semantic conventions), version expectations, and testable acceptance criteria.
- **Testing contract:** [docs/TESTING_SPEC.md](docs/TESTING_SPEC.md) — pytest commands, success/failure/exporter-error scenarios, in-memory fakes, replayt public-surface-only rule, and CI parity.
- **CI contract:** [docs/CI_SPEC.md](docs/CI_SPEC.md) — Ruff + pytest step naming, exit codes, and log hygiene (matches [DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md) **Observable automation**).
- **Releases:** [docs/RELEASE_ENGINEERING_SPEC.md](docs/RELEASE_ENGINEERING_SPEC.md) — maintainer checklist (**§4**), strategy **B** version sync (**§6.1**), [`.github/workflows/publish-pypi.yml`](.github/workflows/publish-pypi.yml) for tag-gated **OIDC** publish (**§5.2**).
- **Pins and upgrades:** [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§7.6** and **Pinning, SemVer, and breaking changes** below.
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
| Python | `>=3.11` (`requires-python`, **declared** floor) | Job **`test`** in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the **full** four-cell replayt×OpenTelemetry matrix on **3.11** and **3.12** (eight rows on `push` / `pull_request`)—[docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§4.1**, [docs/CI_SPEC.md](docs/CI_SPEC.md) **§3.6** (*requires-python parity*). |
| OpenTelemetry API / SDK | `>=1.20.0,<2` each | `test` **strategy.matrix**: pins **1.20.0** and **1.40.0** (each cell reinstalls API + SDK to the same version); **Print resolved dependency versions** logs `replayt`, `opentelemetry-api`, `opentelemetry-sdk` |
| replayt | `>=0.4.0` (no upper cap yet—see [COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§3**) | Same matrix: **0.4.0** and PyPI **latest** (`pip install --upgrade --force-reinstall replayt`) |
| OTLP HTTP extra (`[otlp]`) | `opentelemetry-exporter-otlp-proto-http>=1.20.0,<2` | Same OpenTelemetry major as API/SDK; install locally with `pip install -e ".[dev,otlp]"` and match a matrix cell if you need parity |
| OTLP gRPC extra (`[otlp-grpc]`) | `opentelemetry-exporter-otlp-proto-grpc>=1.20.0,<2` | Same bounds as **`[otlp]`**; install with `pip install -e ".[dev,otlp-grpc]"` (or `replayt-opentelemetry-exporter[otlp-grpc]`). CI does not reinstall this extra on every matrix row; bounds are checked in **`tests/test_pyproject_dependencies.py`**. |

Matrix updates are validated by [`.github/workflows/ci.yml`](.github/workflows/ci.yml): each qualifying **`push`** / **`pull_request`** runs **Ruff** and **pytest** once per matrix cell (**eight** rows: **3.11** and **3.12** × four replayt×OpenTelemetry combinations). Approximate a cell locally with the Python minor you care about, `pip install -e ".[dev]"`, then `pip install "replayt==0.4.0" "opentelemetry-api==1.20.0" "opentelemetry-sdk==1.20.0"` (or `latest` / `1.40.0` as needed), and `pytest` from the repo root.

## Pinning, SemVer, and breaking changes

**Normative detail:** [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§7.6** (adapter SemVer), **§3** (stable exports / `__all__`), **§5.7** and **§6.8** (when metric, span, and lifecycle names change).

- **Pin this package** — Use an exact version in lockfiles or requirements (for example `replayt-opentelemetry-exporter==0.2.0`) or a bounded range your release process allows (for example `>=0.2.0,<0.3.0`). Pin **replayt** and **OpenTelemetry** separately so they stay within the ranges in **`pyproject.toml`** and [docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md).
- **What SemVer covers here** — Version numbers on **PyPI** for **`replayt-opentelemetry-exporter`** follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) / SemVer as described in [CHANGELOG.md](CHANGELOG.md). They describe **this adapter’s** public surface and documented telemetry identifiers, **not** upstream replayt or OpenTelemetry release policies.
- **First stable line** — **0.2.0** is the first release that ships the stable exporter API and tracing/metrics contract; **0.1.0** was packaging scaffold only ([docs/RELEASE_ENGINEERING_SPEC.md](docs/RELEASE_ENGINEERING_SPEC.md) **§9.1**). Upgrade notes live in the dated CHANGELOG section for your target version.
- **Breaking changes to watch** — Expect a **major** bump when **`__all__`** loses or renames documented symbols (**§3**), or when canonical **metric names**, **default span name**, or **lifecycle events/attributes** change in ways that break **§5.7** / **§6.8** stability rules (dashboards, alerts, and downstream queries). **Minor** releases may add symbols or backward-compatible telemetry; **patch** releases fix bugs without breaking that contract.

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

**CI:** job **`test`** runs the same steps on **Python 3.11** and **3.12** for **each** replayt×OpenTelemetry cell ([docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§4.1**, [docs/CI_SPEC.md](docs/CI_SPEC.md) **§3.6**). There is no **`CONTRIBUTING.md`**; local commands above are the contributor contract.

## Enable tracing and metrics in development

1. Install runtime dependencies (included in the default package) and **one** OTLP transport extra (HTTP or gRPC). You rarely need both in the same environment unless you have a documented reason.

   ```bash
   pip install -e ".[dev,otlp]"          # OTLP over HTTP
   # or
   pip install -e ".[dev,otlp-grpc]"    # OTLP over gRPC
   ```

   For a published wheel: `pip install "replayt-opentelemetry-exporter[otlp]"` or `replayt-opentelemetry-exporter[otlp-grpc]`.

2. Wire a tracer provider and exporter, then use `workflow_run_span` around the integrator-owned block that runs a workflow (for example the code that calls replayt’s `Runner` / `Workflow` / `run_with_mock`). See **§2** and **§3** of [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) for the integration seam and full `__all__` list.

   **OTLP HTTP** (after `pip install -e ".[dev,otlp]"`):

   ```python
   from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
   from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

   from replayt_opentelemetry_exporter import (
       install_tracer_provider,
       install_meter_provider,
       get_workflow_tracer,
       workflow_run_span,
   )

   install_tracer_provider(span_exporters=[OTLPSpanExporter()])
   install_meter_provider(metric_exporters=[OTLPMetricExporter()])

   tracer = get_workflow_tracer()
   with workflow_run_span(tracer, "my-workflow-id", run_id="optional-run-id"):
       ...  # e.g. replayt Runner / Workflow invocation
   ```

   **OTLP gRPC** (after `pip install -e ".[dev,otlp-grpc]"`):

   ```python
   from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
   from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

   from replayt_opentelemetry_exporter import (
       install_tracer_provider,
       install_meter_provider,
       get_workflow_tracer,
       workflow_run_span,
   )

   install_tracer_provider(span_exporters=[OTLPSpanExporter()])
   install_meter_provider(metric_exporters=[OTLPMetricExporter()])

   tracer = get_workflow_tracer()
   with workflow_run_span(tracer, "my-workflow-id", run_id="optional-run-id"):
       ...  # e.g. replayt Runner / Workflow invocation
   ```

3. **Endpoints and protocol** — Set `OTEL_EXPORTER_OTLP_ENDPOINT` to your collector (for example a Jaeger OTLP URL). For traces or metrics alone, you can use `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` / `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`. If the collector or defaults assume the wrong transport, set `OTEL_EXPORTER_OTLP_PROTOCOL`, or `OTEL_EXPORTER_OTLP_TRACES_PROTOCOL` / `OTEL_EXPORTER_OTLP_METRICS_PROTOCOL`, to `http/protobuf` or `grpc` as required. Full variable lists live in the [OpenTelemetry environment variable spec](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/) and your exporter package docs.

4. **HTTP vs gRPC** — **HTTP** fits many setups behind L7 load balancers, restrictive proxies, and some gateway-only or serverless paths. **gRPC** is common with Kubernetes-oriented collectors, some vendor stacks, and HTTP/2-native paths. **TLS** works for both; **mTLS** and corporate PKI follow your OpenTelemetry distro and platform docs.

5. Confirm spans named `replayt.workflow.run` with attributes `replayt.workflow.id` / `replayt.run.id` appear in your backend. Verify span **events** `replayt.workflow.run.started` and `replayt.workflow.run.completed` and completion attributes such as `replayt.workflow.outcome` (and on failures `replayt.workflow.error.type` / `replayt.workflow.failure.category`) so operators can see run start and outcome without reading raw exception messages in attributes. Names and semantics are defined in [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§6**; **§6.8** states how those names relate to OpenTelemetry trace conventions and rename policy.

For tests or custom wiring without touching the global provider, use `build_tracer_provider` and `build_meter_provider` and obtain a tracer/meter via `provider.get_tracer(...)` or `provider.get_meter(...)`. For in-process metric assertions, pass `metric_readers=[InMemoryMetricReader()]` to `build_meter_provider`; OTLP and similar backends keep using `metric_exporters`.

## Metrics

Canonical **instrument names**, types, and semantics are defined in **[docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §5**; the **[CHANGELOG.md](CHANGELOG.md)** section dated for your installed version lists what shipped, and **Unreleased** holds merged work not yet on PyPI. **§5.7** covers meter scope, resource keys, and how those names relate to OpenTelemetry metrics and resource conventions. Summary:

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

**[docs/OPERATOR_RUNBOOK.md](docs/OPERATOR_RUNBOOK.md)** — PromQL-style examples, Grafana panel intents, and alert starting points for the §5 metrics, aligned with [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§5–§6** and **§5.7** / **§6.8** (label semantics, cardinality, and naming vs OpenTelemetry conventions). Confirm metric and label names on your OTLP → Prometheus (or vendor) pipeline before copying queries verbatim.

Normative checklist and backlog mapping: **[docs/OPERATOR_MONITORING_SPEC.md](docs/OPERATOR_MONITORING_SPEC.md)**.

## Releases and PyPI (maintainers)

**Normative spec:** [docs/RELEASE_ENGINEERING_SPEC.md](docs/RELEASE_ENGINEERING_SPEC.md) — maintainer checklist (**§4**), **`python -m build`** + **`twine check`**, **tag** naming (**§6.2**), **CHANGELOG** cut rules (**§6.3**), and **GitHub Actions** for **OIDC trusted publishing** (**§5.2**). The package name on PyPI is **`replayt-opentelemetry-exporter`** (from **`pyproject.toml`** **`[project].name`**).

**Version (strategy B):** The distribution version is **`[project].version`** in **`pyproject.toml`** only. **`replayt_opentelemetry_exporter.__version__`** reads **`importlib.metadata.version("replayt-opentelemetry-exporter")`** so there is no second literal to drift. **`tests/test_version_sync.py`** enforces equality between **`pyproject.toml`**, installed metadata, and **`__version__`**.

**After publish:** To confirm [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§8** item **17** against the live index, run **`VERIFY_PYPI_INDEX=1 pytest tests/test_pypi_index.py -q`**. Default **`pytest`** skips that module so PR CI stays offline-safe until the project exists on PyPI.

**Local build and check** (after `pip install -e ".[dev]"` so **`build`** and **`twine`** are available):

```bash
python -m build
twine check dist/*
```

**Publish on PyPI:** Workflow [`.github/workflows/publish-pypi.yml`](.github/workflows/publish-pypi.yml) runs on **`vMAJOR.MINOR.PATCH`** tags (for example **`v0.2.0`**). It builds with **`python -m build`** and uploads using **`pypa/gh-action-pypi-publish`** with **OIDC**; the default path does **not** use a long-lived **`PYPI_API_TOKEN`** repository secret. First-time maintainers register the GitHub repo and workflow in the PyPI project’s **trusted publisher** settings; see [PyPI trusted publishers](https://docs.pypi.org/trusted-publishers/).

**GitHub milestones:** This repository does not use GitHub Milestones (or Projects) for release buckets; **[docs/RELEASE_ENGINEERING_SPEC.md](docs/RELEASE_ENGINEERING_SPEC.md) §9.3** is **N/A** here unless that policy changes.

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
