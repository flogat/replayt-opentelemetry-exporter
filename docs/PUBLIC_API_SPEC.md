# Public API and replayt integration seam

This document is the **specification** for backlog item *Define public exporter API and replayt integration seam*.  
Implementations MUST match it before we treat the API as stable for integrators. For design philosophy (narrow surfaces, consumer-side maintenance), see [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md).

## 1. Purpose

Integrators need a **small, documented** way to attach OpenTelemetry **traces and metrics** to replayt workflow runs at **clear run boundaries**, without changing replayt core. This package provides that as an optional adapter.

### 1.1 Backlog acceptance mapping

The backlog item *Define public exporter API and replayt integration seam* is satisfied for documentation when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Public API listed with minimal examples | **README** ([Enable tracing and metrics in development](../README.md#enable-tracing-and-metrics-in-development)), **§3** (symbol table), **§3.3** (normative example) |
| Run-boundary behavior (start/end, error path) | **§4** (span lifecycle, ordered steps, re-raise rule) |
| Version expectations (or explicit TODO where unavoidable) | **§7** and README **Version compatibility**; TODOs only for unknown upper bounds |

## 2. Replayt integration seam

### 2.1 What this package owns

- **Consumer-side** wiring only: call sites in the integrator’s application (or thin wrapper) invoke this package’s APIs around work that constitutes a “workflow run.”
- **No requirement** that replayt core exposes OTel hooks. The seam is: **your code** that starts and finishes a run (or handles failure) calls into this package.

### 2.2 Suggested touchpoints (replayt public surface)

Replayt’s public API includes types such as `Workflow`, `Runner`, `RunContext`, `RunResult`, and helpers like `run_with_mock` (see replayt’s own docs and `__all__` for the version you use). Integrators SHOULD wrap the **narrowest** block that corresponds to one logical run—for example:

- Around the invocation of `Runner` methods that execute a workflow through to completion or failure, or
- Around `run_with_mock` (or equivalent) when that is the integration’s unit of work.

Exact call sites are **application-specific**. This repository MUST document the pattern (see §4) and MAY add examples that use replayt types **without** implying a private replayt API.

### 2.3 Out of scope for the seam

- Monkey-patching or forking replayt to inject instrumentation.
- Defining replayt’s internal lifecycle; we only define **when our span and metrics APIs run** relative to integrator-controlled boundaries.

## 3. Stable public Python API

The importable package is **`replayt_opentelemetry_exporter`**. The following symbols MUST be exported from the package’s top level (i.e. appear in `__all__` in `src/replayt_opentelemetry_exporter/__init__.py`) once the implementation is complete.

| Symbol | Role |
| ------ | ---- |
| `__version__` | Package version string. |
| `build_resource` | Build `Resource` for tracer/meter providers (service name, optional extra attributes). |
| `build_tracer_provider` | Construct `TracerProvider` with optional `SpanExporter` list (no global side effects). |
| `build_meter_provider` | Construct `MeterProvider` with optional `MetricExporter` list (wrapped in periodic readers) and/or optional `MetricReader` list attached as-is—for example `InMemoryMetricReader` in tests (no global side effects). |
| `install_tracer_provider` | Install tracer provider on the global `opentelemetry.trace` API. |
| `install_meter_provider` | Install meter provider on the global `opentelemetry.metrics` API. Accepts the same exporter/reader options as `build_meter_provider`. |
| `get_workflow_tracer` | Return a `Tracer` from the **currently installed** global tracer provider, using a **stable instrumentation scope name** (implementation-defined string that MUST stay stable across minor releases—see §3.1). |
| `workflow_run_span` | Context manager: one OpenTelemetry span for a single workflow run, with metrics side effects as specified in §4. |
| `RunSummary` | Dataclass for a safe, non-secret run summary (see [RUN_SUMMARY_SPEC.md](RUN_SUMMARY_SPEC.md)). |
| `generate_run_summary` | Build a `RunSummary` from span and run metadata (see [RUN_SUMMARY_SPEC.md](RUN_SUMMARY_SPEC.md)). |
| `record_run_outcome` | Record run outcome metrics when the integrator does not use `workflow_run_span` for the whole run (advanced; requires a meter provider whose instruments were created by `build_meter_provider` / `install_meter_provider`). |
| `record_exporter_error` | Record exporter health / export failure signals (advanced; same meter-provider requirement as `record_run_outcome`). |

### 3.1 `get_workflow_tracer` instrumentation scope

`get_workflow_tracer()` MUST resolve its `Tracer` via `opentelemetry.trace.get_tracer(name)` (or equivalent) using a **single stable scope string** for this package. Patch releases MAY not rename that string; if it changes in a minor release, document the migration in [CHANGELOG.md](../CHANGELOG.md). The current implementation uses the tracing submodule’s `__name__` (`replayt_opentelemetry_exporter.tracing`); treat that as the de facto scope until README lists an explicit constant.

### 3.2 Optional / future-only symbols

If the project later adds more public helpers, they MUST be listed in `__all__` and in this section or the main table before the release ships. Removing any symbol listed in §3 is a **semver-major** change unless it was explicitly marked private (for example a leading underscore) and never documented here.

### 3.3 Minimal integrator example (normative pattern)

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
    # Call replayt Runner / Workflow / run_with_mock here
    ...
```

Optional dependency: OTLP HTTP exporters are not in the core dependency set; integrators install `replayt-opentelemetry-exporter[otlp]` (or an equivalent extra) when using OTLP, per `pyproject.toml`.

## 4. Run-boundary behavior (`workflow_run_span`)

Integrators MUST be able to rely on the following semantics.

### 4.0 Context manager signature (normative)

```text
workflow_run_span(
    tracer: Tracer,
    workflow_id: str,
    *,
    run_id: str | None = None,
    span_name: str = "replayt.workflow.run",
    attributes: dict[str, str] | None = None,
) -> Iterator[Span]
```

| Parameter | Requirement |
| --------- | ----------- |
| `tracer` | OpenTelemetry `Tracer` used to create the run span (typically from `get_workflow_tracer()` after installing a provider). |
| `workflow_id` | Required logical workflow identifier; becomes span attribute `replayt.workflow.id` and low-cardinality metric label `workflow_id`. |
| `run_id` | Optional; when set, span attribute `replayt.run.id` and optional metric label `run_id`. |
| `span_name` | Optional override of the default span name (`replayt.workflow.run`); use for disambiguation only—default keeps backends consistent. |
| `attributes` | Optional extra string attributes merged onto the span after validation against [SECURITY_REDACTION.md](SECURITY_REDACTION.md); until redaction is implemented, document any passthrough as **TODO** in release notes if behavior is permissive. |

The context manager **yields** the active `Span` so callers can attach events or call `generate_run_summary` while the span is open.

### 4.1 Span lifecycle

- **Start:** When the context manager is entered, the implementation starts a span with name `span_name` (default `replayt.workflow.run`).
- **Attributes:** Set at least `replayt.workflow.id` from `workflow_id`. If `run_id` is provided, set `replayt.run.id`. If `attributes` is provided, merge keys after validation (see SECURITY policy; stub validation MAY pass through until implemented—call out in CHANGELOG when tightened).
- **Success:** If the block exits without an exception, set span status to **OK**, end the span, and record **success** outcome metrics (see §5).
- **Failure:** If the block raises, set span status to **ERROR** (with a safe description), call `record_exception` (or equivalent) on the span, end the span, record **failure** outcome metrics, then **re-raise** the exception. Integrators’ error handling is unchanged.

### 4.1.1 Ordered lifecycle (normative sequence)

1. **Enter:** Open a span as the current span (`start_as_current_span` or equivalent).
2. **Annotate:** Apply `replayt.workflow.id`, optional `replayt.run.id`, and validated extra attributes.
3. **Run:** Execute the integrator’s block (`yield` the span).
4. **Success path:** On normal completion, set status OK, compute duration, record success metrics, exit the context manager (span ends).
5. **Error path:** On exception, set status ERROR, `record_exception`, compute duration, record failure metrics, **re-raise** the same exception, then end the span as part of context exit.
6. **Metrics dependency:** Outcome and duration instruments MUST target the global meter provider state established by `install_meter_provider` (or test doubles)—see §4.3.

### 4.2 Nesting and concurrency

- Nesting or overlapping `workflow_run_span` contexts SHOULD be avoided unless the integrator intentionally models sub-runs; behavior in nested cases MUST be documented in code comments or this spec if non-obvious.

### 4.3 Global providers

- `workflow_run_span` uses the `Tracer` passed in; it does not replace the global tracer provider. Metrics that the context manager records depend on a **configured** global meter provider (via `install_meter_provider` or test doubles).

## 5. Metrics (canonical names and semantics)

Published instruments MUST use the names below unless a semver-major release changes them. Attribute keys on metrics SHOULD stay **low-cardinality**; prefer stable workflow identifiers over unbounded labels.

| Instrument (type) | Name | Purpose |
| ----------------- | ---- | ------- |
| Counter | `replayt.workflow.run.outcomes_total` | Count completed runs; distinguish success vs failure via attributes (e.g. `outcome`). |
| Histogram | `replayt.workflow.run.duration_ms` | Run duration in milliseconds. |
| Counter | `replayt.exporter.errors_total` | Export or serialization failures and similar (e.g. `error_type` attribute). |

Exact attribute keys for each instrument are listed in the [README](../README.md) **Metrics** section. This table is the normative instrument list; [CHANGELOG.md](../CHANGELOG.md) **Unreleased** records notable naming or semantics changes between releases.

## 6. Trace semantics (span naming)

- Default span name: `replayt.workflow.run`.
- Required attributes: `replayt.workflow.id`; optional `replayt.run.id` when the integrator has a run identifier.

## 7. Version and compatibility expectations

### 7.1 Declared in `pyproject.toml` (normative ranges)

- **Python:** `requires-python` as specified in `[project]` (currently `>=3.11`).
- **OpenTelemetry:** `opentelemetry-api` and `opentelemetry-sdk` lower bounds as in `[project.dependencies]` (currently `>=1.20.0`). Integrators MAY use newer API/SDK minors on the same major line; this package SHOULD stay compatible with supported OTel majors per release notes.
- **replayt:** Lower bound as in `[project.dependencies]` (currently `>=0.1.0`). Upper bounds or caps MAY be added for known breakages.

### 7.2 Tested / documented matrix (maintenance obligation)

- CI or release documentation SHOULD record at least one **tested** replayt version (e.g. the version installed in CI or printed in the workflow log).
- **Mission Control baseline (phase 1c):** replayt **0.4.25** was installed when the backlog pipeline last captured dependency output; treat that as the **reference** public API snapshot for examples (`Workflow`, `Runner`, `RunContext`, `run_with_mock`, etc.) until CI pins otherwise.
- When this repository claims support for a specific replayt line in README, update examples and §2.2 in the same release branch—**no TODO** for touchpoints once that version is advertised.

### 7.3 Compatibility snapshot (copy for releases)

Values below mirror `[project]` / `[project.dependencies]` in `pyproject.toml` at spec time; **maintainers update this table** when bounds change.

| Component | Declared bound | Notes |
| --------- | ---------------- | ----- |
| Python | `requires-python` (currently `>=3.11`) | CI matrices may test a subset. |
| OpenTelemetry API/SDK | `>=1.20.0` | Same major line expected; document any new major in CHANGELOG. |
| replayt | `>=0.1.0` | Upper cap **TODO** until a known-breaking replayt release is identified and tested. |
| Tested replayt (reference) | **0.4.25** (baseline log) | Replace with “CI pinned” version when `ci.yml` or lockfiles fix a version. |

### 7.4 TODO allowed

- Exact **upper** bounds for replayt or OTel when upstream has not yet published a breaking release: MAY remain `TODO` in [CHANGELOG.md](../CHANGELOG.md) or here until validated.

## 8. Acceptance criteria (for Builder / QA)

The **documentation** backlog (phase 2) is complete when §1.1 holds. The **implementation** backlog (phase 3 onward) is complete when all of the following are true:

1. **Public API listed** — README links to this document and shows a minimal end-to-end example consistent with §3.3.
2. **`__all__` matches §3** — Every symbol named in the §3 table appears in package `__all__`.
3. **Run boundaries** — Behavior matches §4 (success path, error path with re-raise, span ended, metrics recorded per §4.1.1).
4. **Versions** — README and §7 state dependency ranges from `pyproject.toml` and the tested/reference replayt line per §7.2–7.3.
5. **Tests** — Pytest passes without merge artifacts; tests cover span attributes, success/failure metrics, and provider installation at least at the level of `tests/test_tracing.py` intent.
6. **Docs consistency** — README metric names and descriptions align with §5 and [CHANGELOG.md](../CHANGELOG.md) **Unreleased** entries after implementation.

## 9. Related documents

- [MISSION.md](MISSION.md) — Scope and audiences.
- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) — Narrow APIs and consumer-side maintenance.
- [RUN_SUMMARY_SPEC.md](RUN_SUMMARY_SPEC.md) — `RunSummary` / `generate_run_summary`.
- [SECURITY_REDACTION.md](SECURITY_REDACTION.md) — What MUST NOT appear in attributes or summaries.
