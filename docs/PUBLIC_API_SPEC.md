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

The backlog item *Add compatibility matrix and dependency pins for replayt and OpenTelemetry* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| README or docs table lists supported replayt and OTel versions | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§2**; README **Version compatibility** (table or link) |
| `pyproject.toml` declares runtime dependencies with justified bounds | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§3**; **§7.1** here (normative ranges) |
| Changelog or docs note how matrix updates are validated | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4**; [CHANGELOG.md](../CHANGELOG.md) when behavior ships |

Full automation (CI matrix) is specified in **COMPATIBILITY_MATRIX_SPEC.md §4**; implementing it is **Builder** work, not Spec-only.

The backlog item *Emit traces for replayt workflow run lifecycle with human-readable status* is satisfied for documentation when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Spans cover run start, success, and failure paths | **§6** (trace shape, lifecycle events, completion attributes) |
| Failure surfaces use OTel status and/or safe, readable attributes | **§6.3**–**§6.4** (status, `replayt.workflow.outcome`, `replayt.workflow.error.type`, `replayt.workflow.failure.category`) |
| No sensitive values in default lifecycle attributes | **§6.5** and [SECURITY_REDACTION.md](SECURITY_REDACTION.md) |

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
| `attributes` | Optional extra string attributes merged onto the span after validation against [SECURITY_REDACTION.md](SECURITY_REDACTION.md) (blocked keys omitted, long values truncated; see that document). |

The context manager **yields** the active `Span` so callers can attach events or call `generate_run_summary` while the span is open.

### 4.1 Span lifecycle

- **Start:** When the context manager is entered, the implementation starts a span with name `span_name` (default `replayt.workflow.run`).
- **Attributes:** Set at least `replayt.workflow.id` from `workflow_id`. If `run_id` is provided, set `replayt.run.id`. If `attributes` is provided, merge keys after validation (see SECURITY policy and [CHANGELOG.md](../CHANGELOG.md) when rules change).
- **Success:** If the block exits without an exception, set span status to **OK**, apply **§6** lifecycle attributes and completion events, compute duration, record **success** outcome metrics (see §5), then end the span when the context manager exits (same ordering as §4.1.1 step 4).
- **Failure:** If the block raises, call `record_exception` (or equivalent) on the span, set span status to **ERROR** with a **safe description** (exception type name only—no arbitrary `str(exc)` text), apply **§6** lifecycle attributes and completion events, compute duration, record **failure** outcome metrics, **re-raise** the same exception, then end the span when the context manager exits (same ordering as §4.1.1 step 5). The implementation turns off OpenTelemetry’s default `set_status_on_exception` / automatic exception recording on the run span so the library’s status line is not overwritten with the full exception message when the context exits. Integrators’ error handling is unchanged.

### 4.1.1 Ordered lifecycle (normative sequence)

1. **Enter:** Open a span as the current span (`start_as_current_span` or equivalent).
2. **Annotate:** Apply `replayt.workflow.id`, optional `replayt.run.id`, and validated extra attributes.
3. **Run:** Execute the integrator’s block (`yield` the span).
4. **Success path:** On normal completion, set span attributes and completion **span events** per **§6**, set status OK, compute duration, record success metrics, exit the context manager (span ends).
5. **Error path:** On exception, `record_exception`, set span attributes and completion **span events** per **§6**, set status ERROR with a safe description (exception type only), compute duration, record failure metrics, **re-raise** the same exception, then end the span as part of context exit (OTel auto status/exception hooks for this span are disabled so the safe description survives re-raise).
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

### 5.1 Normative instrument list

The table above is the canonical instrument set. [CHANGELOG.md](../CHANGELOG.md) **Unreleased** records notable naming or semantics changes between releases.

### 5.2 Attribute keys

A short summary of label keys lives in the [README](../README.md) **Metrics** section. Cardinality expectations are in §5.4.

### 5.3 `error_type` (`replayt.exporter.errors_total`)

Use one of: `export_failed`, `serialization_error`, `timeout`, `unknown`. The implementation records only these values on the metric: any other string is stored as `unknown`, and the caller-supplied string is logged at debug level. That keeps time series bounded while older call sites that passed ad hoc strings keep working.

### 5.4 Cardinality

- `workflow_id`: keep to a stable, small set per deployment (operator guidance: tens to low hundreds of distinct values).
- `outcome`: two values (`success`, `failure`).
- `run_id`: optional; do not use unbounded unique values as a routine label.
- `error_type`: four values after normalization (§5.3).

### 5.5 Advanced recording APIs

`record_run_outcome` and `record_exporter_error` support integrators who do not wrap the full run in `workflow_run_span`. They require a meter provider whose instruments were created through this package’s `build_meter_provider` / `install_meter_provider` (or test doubles that register the same instrument names).

### 5.6 Exemplars

Histogram exemplars are optional. Turn them on only when organizational policy allows and labels follow [SECURITY_REDACTION.md](SECURITY_REDACTION.md).

## 6. Workflow run trace lifecycle and human-readable status

This section is the **specification** for backlog item *Emit traces for replayt workflow run lifecycle with human-readable status*. It normatively extends **§4** so operators and backends see **run start**, **milestones** (where recorded), and **completion** (success or failure) with **stable, low-cardinality** signals suitable for dashboards—without putting sensitive text in default span or event attributes.

### 6.1 Goals

- **Operators** can tell *that a run started*, *how it ended*, and *what class of failure* occurred without reading raw exception messages in attributes.
- **Backends and UIs** can filter and group on documented attribute keys and event names (see **§6.6**).
- **Defaults** stay aligned with [SECURITY_REDACTION.md](SECURITY_REDACTION.md): no credentials, prompts, or arbitrary exception text in lifecycle attributes or event attribute values.

### 6.2 Trace shape (normative)

- **Root span:** Exactly one root run span per `workflow_run_span` invocation, named `span_name` (default `replayt.workflow.run` per §4.0). Nested child spans are **optional** and **out of scope** for this backlog unless a future spec adds them; **milestones use span events** on this root span unless otherwise documented.
- **Run start:** When the context manager opens the span, the implementation MUST add a span **event** named `replayt.workflow.run.started` (no required attributes—the workflow and run identifiers already live on the span as `replayt.workflow.id` / `replayt.run.id`).
- **Milestones (during the run):** When the adapter observes replayt lifecycle hooks or when integrators record milestones through a **documented extension** (see §6.2.1), the implementation SHOULD add span **events** named `replayt.workflow.milestone` with attribute **`replayt.workflow.milestone.name`** whose value is a **low-cardinality** token from **§6.2.2** or another token that obeys **§6.6**. Milestones are **best-effort** until replayt surfaces are wired; the **minimum** required signals remain **started** + **completed** events and completion attributes.
- **Completion (success):** Before the span ends on the success path, the implementation MUST set span attribute **`replayt.workflow.outcome`** = `success` and add a span **event** named `replayt.workflow.run.completed` with attribute **`replayt.workflow.outcome`** = `success` on the event.
- **Completion (failure):** Before re-raising, the implementation MUST set span attributes **`replayt.workflow.outcome`** = `failure` and **`replayt.workflow.error.type`** = the exception’s **type name** (same string as the OTel status description in §4.1), SHOULD set **`replayt.workflow.failure.category`** per **§6.4**, and MUST add a span **event** named `replayt.workflow.run.completed` carrying the same **`replayt.workflow.outcome`**, **`replayt.workflow.error.type`**, and (when set) **`replayt.workflow.failure.category`** on the event. Do **not** put `str(exception)` or stack text in these attributes or event attributes.

#### 6.2.1 Integrator-recorded milestones

Until the package provides a dedicated helper, integrators MAY call `Span.add_event` on the span yielded by `workflow_run_span` to emit `replayt.workflow.milestone` events using the attribute rules above. If the package later adds a public helper (for example `record_workflow_milestone`), it MUST validate or normalize names per **§6.2.2** / **§6.6** and MUST be listed in **§3** before release.

#### 6.2.2 Recommended `replayt.workflow.milestone.name` values

These tokens are **recommended** for consistency across deployments; implementations and integrators MAY add **new** tokens only when they remain **low-cardinality** (operator guidance: tens of distinct values per deployment, not unbounded user strings).

| Value | Meaning (informative) |
| ----- | --------------------- |
| `invoked` | Run/workflow execution handed to replayt (or equivalent entry). |
| `awaiting_approval` | Run is blocked on human or external approval, if applicable. |
| `executing` | Active execution phase. |
| `finalizing` | Post-processing or cleanup before completion. |

### 6.3 Span status vs attributes (human-readable)

| Signal | Success path | Failure path |
| ------ | ------------ | ------------ |
| OTel **span status** | `StatusCode.OK` | `StatusCode.ERROR`, **description** = exception **type name** only (e.g. `ValueError`) — same rule as §4.1 |
| Span attribute **`replayt.workflow.outcome`** | `success` | `failure` |
| Span attribute **`replayt.workflow.error.type`** | *(omit)* | Exception **type name** (mirrors status description) |
| Span attribute **`replayt.workflow.failure.category`** | *(omit)* | One of **§6.4** (recommended for dashboards) |

Exception **events** (`record_exception`) may still carry message/stack per the SDK; treat that like other sensitive telemetry per [SECURITY_REDACTION.md](SECURITY_REDACTION.md).

### 6.4 Failure category (`replayt.workflow.failure.category`)

On failure, the implementation SHOULD set **`replayt.workflow.failure.category`** on the span and on the `replayt.workflow.run.completed` event to **one** of the following **normalized** values so UIs can bucket failures without parsing messages:

| Value | Intended use |
| ----- | ------------ |
| `validation` | Invalid inputs, schema, or preconditions (e.g. `ValueError`, `TypeError`, `ContextSchemaError` when used as validation). |
| `timeout` | Time limits exceeded (`TimeoutError` and similar). |
| `cancelled` | Cooperative cancellation (`CancelledError` / task cancelled). |
| `external_dependency` | Upstream I/O or third-party failures (e.g. connection errors), when distinguishable without logging secrets. |
| `runtime` | Other programmatic errors not better classified above. |
| `unknown` | Default when classification is not implemented or ambiguous. |

Exact **exception-type → category** mapping is **implementation-defined** but MUST be **documented in source comments** and MUST **not** introduce secret or high-cardinality values. Replayt-specific types (for example `RunFailed`, `ApprovalPending`) SHOULD map to the closest category; refine mappings in patch releases without breaking attribute **keys**.

### 6.5 Sensitive data (lifecycle)

Lifecycle **span attributes** and **event attributes** defined in this section MUST NOT include: raw user input, prompts, completions, credentials, tokens, full exception messages, or unbounded stack text. Follow [SECURITY_REDACTION.md](SECURITY_REDACTION.md) for optional integrator-supplied attributes merged via §4.0.

### 6.6 Cardinality and dashboard guidance

- **Low-cardinality keys** suitable for filters, breakdowns, and alerts: `replayt.workflow.id` (per deployment policy), `replayt.workflow.outcome`, `replayt.workflow.failure.category`, `replayt.workflow.error.type` (bounded by code), event names `replayt.workflow.run.started`, `replayt.workflow.run.completed`, `replayt.workflow.milestone`.
- **`replayt.run.id`:** Optional on the span; do not use unbounded unique values as a **routine** high-cardinality dashboard dimension unless your backend policy allows it.
- **Span name:** Default `replayt.workflow.run` remains the primary trace selector for “one workflow run.”

### 6.7 Span naming (summary)

- Default span name: `replayt.workflow.run` (override per §4.0 only when disambiguation is needed).
- Required span attributes (existing §4): `replayt.workflow.id`; optional `replayt.run.id` when the integrator supplies a run identifier.
- Completion attributes **`replayt.workflow.outcome`** (and failure-only keys above) are **in addition** to §4’s required keys.

## 7. Version and compatibility expectations

**Compatibility matrix, pin justification, and CI validation policy** are specified in **[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md)**. This section stays the short normative snapshot for integrators; avoid duplicating matrix maintenance rules here.

### 7.1 Declared in `pyproject.toml` (normative ranges)

- **Python:** `requires-python` as specified in `[project]` (currently `>=3.11`).
- **OpenTelemetry:** `opentelemetry-api` and `opentelemetry-sdk` lower bounds as in `[project.dependencies]` (currently `>=1.20.0`). Integrators MAY use newer API/SDK minors on the same major line; this package SHOULD stay compatible with supported OTel majors per release notes.
- **replayt:** Lower bound as in `[project.dependencies]` (currently `>=0.1.0`). Upper bounds or caps MAY be added for known breakages.

### 7.2 Tested / documented matrix (maintenance obligation)

- Until a **multi-version matrix** lands (see [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4**), CI prints the resolved **replayt** version after `pip install` (see `.github/workflows/ci.yml` `test` job step **Print replayt version**). That line is the **single tested resolver outcome** for that workflow run.
- **Mission Control baseline (phase 1c):** replayt **0.4.25** was installed when the backlog pipeline last captured dependency output; treat that as the **reference** public API snapshot for examples (`Workflow`, `Runner`, `RunContext`, `run_with_mock`, etc.) until README and the compatibility matrix claim a different line.
- When this repository claims support for a specific replayt line in README or [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md), update examples and §2.2 in the same release branch—**no TODO** for touchpoints once that version is advertised.

### 7.3 Compatibility snapshot (copy for releases)

Values below mirror `[project]` / `[project.dependencies]` in `pyproject.toml` at spec time; **maintainers update this table** when bounds change.

| Component | Declared bound | Notes |
| --------- | ---------------- | ----- |
| Python | `requires-python` (currently `>=3.11`) | CI matrices may test a subset. |
| OpenTelemetry API/SDK | `>=1.20.0` | Same major line expected; document any new major in CHANGELOG. |
| replayt | `>=0.1.0` | Upper cap **TODO** until a known-breaking replayt release is identified and tested. |
| Tested replayt (CI) | Printed in CI after install | Latest satisfying `>=0.1.0` unless you add a pin or lockfile. |
| Reference replayt (examples) | **0.4.25** (baseline log) | Update when README claims a different line. |

### 7.4 TODO allowed

- Exact **upper** bounds for replayt or OTel when upstream has not yet published a breaking release: MAY remain `TODO` in [CHANGELOG.md](../CHANGELOG.md), here, or [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) until validated—provided **§3** of that document still records rationale for existing lower bounds.

## 8. Acceptance criteria (for Builder / QA)

The **documentation** backlog (phase 2) is complete when §1.1 holds (both mapped backlog items). The **implementation** backlog (phase 3 onward) is complete when all of the following are true:

1. **Public API listed** — README links to this document and shows a minimal end-to-end example consistent with §3.3.
2. **`__all__` matches §3** — Every symbol named in the §3 table appears in package `__all__`.
3. **Run boundaries** — Behavior matches §4 (success path, error path with re-raise, span ended, metrics recorded per §4.1.1).
4. **Lifecycle traces** — `workflow_run_span` emits the **§6** lifecycle events (`replayt.workflow.run.started`, `replayt.workflow.run.completed`) and sets **§6** completion span attributes on success and failure paths; failure path keeps OTel ERROR status with a **safe** description (exception type only) and sets **`replayt.workflow.failure.category`** per **§6.4** (`unknown` when no mapping applies).
5. **Versions** — README and §7 state dependency ranges from `pyproject.toml` and the tested/reference replayt line per §7.2–7.3; [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§6** (compatibility matrix backlog) is satisfied for tables, justified bounds, and documented CI validation.
6. **Tests** — Pytest passes without merge artifacts; tests cover span attributes, lifecycle events/attributes per §6, success/failure metrics, and provider installation at least at the level of `tests/test_tracing.py` intent.
7. **Docs consistency** — README metric names, trace verification notes, and descriptions align with §5–§6 and [CHANGELOG.md](../CHANGELOG.md) **Unreleased** entries after implementation.

## 9. Related documents

- [MISSION.md](MISSION.md) — Scope and audiences.
- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) — Narrow APIs and consumer-side maintenance.
- [RUN_SUMMARY_SPEC.md](RUN_SUMMARY_SPEC.md) — `RunSummary` / `generate_run_summary`.
- [SECURITY_REDACTION.md](SECURITY_REDACTION.md) — What MUST NOT appear in attributes or summaries; lifecycle defaults (**§6**).
