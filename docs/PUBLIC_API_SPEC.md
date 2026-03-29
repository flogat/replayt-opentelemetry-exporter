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

The backlog item *Validate OpenTelemetry 2.x and document policy* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Current **1.x** bounds and **2.x** cap (or post-validation range) are stated for integrators | **§7.1**, **§7.3** (snapshot table), **§7.4** |
| Spike workflow, documentation outcomes for **support vs exclusion**, and **CI matrix gating** for **2.x** | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7** |
| README and compatibility matrix stay consistent when bounds change | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§2**–**§3**; README **Version compatibility** |

Implementing the spike, widening `pyproject.toml`, extending **`.github/workflows/ci.yml`**, and adjusting **`tests/test_pyproject_dependencies.py`** are **Builder** work; **§8** item **12** is the implementation checklist.

The backlog item *Emit traces for replayt workflow run lifecycle with human-readable status* is satisfied for documentation when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Spans cover run start, success, and failure paths | **§6** (trace shape, lifecycle events, completion attributes) |
| Failure surfaces use OTel status and/or safe, readable attributes | **§6.3**–**§6.4** (status, `replayt.workflow.outcome`, `replayt.workflow.error.type`, `replayt.workflow.failure.category`) |
| No sensitive values in default lifecycle attributes | **§6.5** and [SECURITY_REDACTION.md](SECURITY_REDACTION.md) |

The backlog item *Implement automated tests for replayt boundary and exporter behavior* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Documented test command (e.g. pytest) and CI parity | [TESTING_SPEC.md](TESTING_SPEC.md) **§3**; README **Running tests and lint locally**; [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4** |
| At least one success and one failure / export-error scenario | [TESTING_SPEC.md](TESTING_SPEC.md) **§4.3–§4.5** |
| Clear exit codes for automation | [TESTING_SPEC.md](TESTING_SPEC.md) **§3.3** |

Full test implementation is **Builder** work; this document’s §8 item **6** and [TESTING_SPEC.md](TESTING_SPEC.md) **§5** state the checklist.

The backlog item *Add CI with ruff, tests, and readable logs* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Workflow runs Ruff and pytest (or documented equivalent) | [CI_SPEC.md](CI_SPEC.md) **§3.1**; [TESTING_SPEC.md](TESTING_SPEC.md) **§3**; README **Running tests and lint locally** |
| Failures show which command failed; logs avoid secret dumps | [CI_SPEC.md](CI_SPEC.md) **§3.2–§3.4** |
| README links to or describes the CI entry point | [CI_SPEC.md](CI_SPEC.md) **§3.5**; README links to `.github/workflows/ci.yml` and this spec |

Implementing or adjusting workflow YAML is **Builder** work; [CI_SPEC.md](CI_SPEC.md) **§5** is the checklist.

The backlog item *Expand CI matrix with optional Python 3.11 job* is **superseded** for merge-gate expectations by *Expand CI matrix to include Python 3.11 (requires-python parity)* below. [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.3** records the historical transitional layout only.

The backlog item *Expand CI matrix to include Python 3.11 (requires-python parity)* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| **Declared** Python (`requires-python`) vs **tested** minors (merge gate) are explicit | README **Version compatibility**; [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1**–**§4.2** item **4**; **§7.2**–**§7.3** here |
| **3.11** runs the **same** four replayt×OpenTelemetry cells as **3.12** on **`push` / `pull_request`** | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1**; [CI_SPEC.md](CI_SPEC.md) **§2.2**, **§3.6** |
| Ruff and pytest invocations match README / **§3.1** on every cell (no `CONTRIBUTING.md` in repo) | [CI_SPEC.md](CI_SPEC.md) **§3.1**, **§2.2** (contributor surface); README **Running tests and lint locally** |

Workflow YAML, **`tests/test_ci_workflow.py`**, and CHANGELOG when behavior ships are **Builder** work; **§8** item **14** is the implementation checklist.

The backlog item *Curate docs/reference-documentation from replayt public API* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Bounded markdown (or scripted regeneration) for replayt **Workflow**, **Runner**, **RunContext**, **run_with_mock**, version-stamped to matrix replayt pins | [REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md) **§2–§4** |
| Links from README and **REPLAYT_ECOSYSTEM_IDEA.md** | [REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md) **§5** |
| Alignment with compatibility matrix replayt versions | [REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md) **§4**; [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1** |

Authoring **`docs/reference-documentation/`** and optional **`scripts/`** tooling is **Builder** work; this §1.1 row is the documentation contract.

The backlog item *Integration example: Runner-based workflow beyond run_with_mock* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Documented minimal example uses **`Runner.run`** (not only `run_with_mock`) inside **`workflow_run_span`**, per **§2.2.1** and **§3.4** | **§2.2.1**, **§3.4** (deliverable path and content rules) |
| Uses **only** symbols exposed in replayt’s public surface (`__all__` for the matrix pin you target—see **`docs/reference-documentation/`**) | **§3.4**; [REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md) |
| States the **narrowest** integrator-owned run boundary for production-style apps | **§2.2.1** |
| **Runnable** proof: copy-pastable snippet that runs after `pip install -e ".[dev]"` **or** a pytest contract marked per [TESTING_SPEC.md](TESTING_SPEC.md) **§4.2** | **§3.4**; [TESTING_SPEC.md](TESTING_SPEC.md) **§4.2** |

Authoring **`docs/examples/runner_workflow_run_span.md`** (and optional **`examples/`** script), extending **`tests/`**, and README cross-links are **Builder** work; this §1.1 table is the documentation contract.

The backlog item *Document operator dashboards for canonical metrics* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Operator-facing runbook maps §5 metrics to PromQL/Grafana/alert guidance without reading `tracing.py` | [OPERATOR_MONITORING_SPEC.md](OPERATOR_MONITORING_SPEC.md) **§3–§7**; delivered as **`docs/OPERATOR_RUNBOOK.md`** (or README equivalent per that spec) |
| Label semantics and cardinality match the public API | [OPERATOR_MONITORING_SPEC.md](OPERATOR_MONITORING_SPEC.md) **§2**, **§4**; normative source **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §5–§6** |

Authoring **`docs/OPERATOR_RUNBOOK.md`** and README links is **Builder** work; this §1.1 row is the documentation contract.

The backlog item *Release engineering: PyPI publish and version sync* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Repeatable release steps (tag, build, upload) and **CHANGELOG** / version discipline | [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) **§4**, **§6.3** |
| **Single source of truth** for distribution version and **`__version__`** | [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) **§6**; **§3** here (`__version__` export) |
| **Tag-gated** GitHub Actions with **trusted publishing** | [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) **§5.2**, **§7**; **`.github/workflows/publish-pypi.yml`** |

Implementing **`pyproject.toml` / `__init__.py` changes**, **`python -m build`**, **twine**, **publish workflow YAML**, and **drift tests** is **Builder** work; this §1.1 row and [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) **§7** are the contracts.

The backlog item *Semantic conventions review for span and metric names* is satisfied for **documentation** when:

| Backlog acceptance criterion | Where it is specified |
| ---------------------------- | -------------------- |
| Canonical span names, span events, span attribute keys, metric instrument names, meter scope, and resource attributes from `build_resource` are inventoried and compared to OpenTelemetry semantic conventions where a relevant stable or widely used convention exists | **§5.7**, **§6.8** |
| Intentional deviations (vendor namespace, lifecycle shape, stability vs upstream churn) and rules for semver when names change are documented | **§5.7**, **§6.8** |
| Design principles point integrators at the normative naming contract | [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) **Explicit contracts** |

Keeping the inventory accurate in source and docs, and renaming instruments or lifecycle identifiers without updating **§5–§6**, **§5.7**, **§6.8**, and consumer-facing docs, is **Builder** debt; **§8** item **15** is the implementation checklist.

## 2. Replayt integration seam

### 2.1 What this package owns

- **Consumer-side** wiring only: call sites in the integrator’s application (or thin wrapper) invoke this package’s APIs around work that constitutes a “workflow run.”
- **No requirement** that replayt core exposes OTel hooks. The seam is: **your code** that starts and finishes a run (or handles failure) calls into this package.

### 2.2 Suggested touchpoints (replayt public surface)

Replayt’s public API includes types such as `Workflow`, `Runner`, `RunContext`, `RunResult`, and helpers like `run_with_mock` (see replayt’s own docs and `__all__` for the version you use). **`docs/reference-documentation/`** holds bounded, version-stamped notes for the primary workflow/run symbols ([REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md)). Integrators SHOULD wrap the **narrowest** block that corresponds to one logical run—for example:

- Around the invocation of `Runner` methods that execute a workflow through to completion or failure, or
- Around `run_with_mock` (or equivalent) when that is the integration’s unit of work.

Exact call sites are **application-specific**. This repository MUST document the pattern (see §4) and MAY add examples that use replayt types **without** implying a private replayt API.

### 2.2.1 Narrowest run boundary for `Runner` (production-style apps)

For integrations that use **`replayt.Runner`** with a real or mock **LLM client** (instead of the `run_with_mock` helper), the **recommended narrowest** block to wrap in **`workflow_run_span`** is the **single** call to **`Runner.run`** (and the same exception-mapping you would apply to a `RunResult` from `run_with_mock`—for example re-raising **`RunFailed`** when the run does not complete—**inside** that block so the span captures success vs failure consistently).

- **Inside the context:** construct the **`Runner`** if you do so immediately before **`run`** *or* reuse a long-lived runner—either way, **`workflow_run_span` MUST enclose `Runner.run(...)`** for the logical run you want one trace/metric series for. Do **not** split one user-visible run across multiple `workflow_run_span` contexts unless you intentionally model sub-runs (see **§4.2**).
- **Outside the context:** workflow definition setup (`Workflow`, steps, `set_initial`), store construction, and global OTel provider installation remain **outside** unless your application defines “one run” to include them (unusual).
- **Teardown:** if your integration calls **`Runner.close`**, either include it inside the same span after **`run`** completes (same logical run) or document why a separate boundary is appropriate—default is **same span** when `close` is part of tearing down that runner instance after the run.

This section **does not** introduce a new public API; it narrows **§2.2** for the **`Runner.run`** path so Builders and integrators align on where lifecycle tracing attaches for real applications.

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

For **`Runner.run`** with the same boundary pattern (in-memory OpenTelemetry and **`MockLLMClient`**), see **§3.4** below.

Optional dependency: OTLP HTTP exporters are not in the core dependency set; integrators install `replayt-opentelemetry-exporter[otlp]` (or an equivalent extra) when using OTLP, per `pyproject.toml`.

### 3.4 Runner-based example (normative deliverable)

The repository **MUST** ship a **minimal**, **integrator-facing** example that mirrors **§3.3** but exercises **`Runner`** and **`Runner.run`** per **§2.2.1** (not only **`run_with_mock`**).

| Requirement | Detail |
| ----------- | ------ |
| **Location** | Primary artifact: **`docs/examples/runner_workflow_run_span.md`**. The Builder **MAY** also add a sibling script under **`examples/`** (repository root) if that improves copy-paste ergonomics; if so, README or the markdown file **MUST** document how to run it. |
| **replayt imports** | Only symbols from replayt’s public API (see **`docs/reference-documentation/`** and the installed package’s **`__all__`**). Typical minimal set: **`Workflow`**, **`RunContext`**, **`Runner`**, **`MockLLMClient`**, **`RunFailed`**, **`RunResult`** as needed—**no** private submodules (e.g. do **not** import **`replayt.persistence`**; use an in-memory **EventStore**-shaped object like the contract tests). |
| **Adapter imports** | **`build_tracer_provider`**, **`build_meter_provider`**, **`get_workflow_tracer`**, **`workflow_run_span`** (or the same install pattern as **§3.3** with in-memory exporters/readers for a self-contained demo). |
| **Narrative** | The markdown **MUST** include a short prose callout restating **§2.2.1** (why **`Runner.run`** sits inside **`workflow_run_span`** and what stays outside). |
| **Runnability** | The example **MUST** be **executable** in one of two ways: **(A)** a fenced Python block (or script) that runs with **`pip install -e ".[dev]"`** and **`python …`** as documented, or **(B)** superseded for execution by a **pytest** contract test that calls **`Runner.run`** inside **`workflow_run_span`**, marked per [TESTING_SPEC.md](TESTING_SPEC.md) **§4.2**. **At least one** of (A) or (B) is mandatory so CI or contributors can verify the snippet. |
| **README** | When the artifact lands, README **MUST** link to **`docs/examples/runner_workflow_run_span.md`** from **Quick start** or **Reference documentation** (same release branch as the file). |

The example **SHOULD** use **`MockLLMClient`** so the snippet stays offline and secret-free; integrators substitute their own **`llm_client`** using the same boundary pattern.

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

### 5.7 OpenTelemetry semantic conventions alignment (metrics and resource)

**Informative baseline:** OpenTelemetry publishes [semantic conventions](https://opentelemetry.io/docs/specs/semconv/) for resources, traces, metrics, and domain areas (including experimental Gen AI signals). This section states how **metrics** and **resource** attributes from this package relate to those conventions.

| Area | This package | Convention alignment |
| ---- | ------------ | -------------------- |
| **Resource** | `build_resource` sets `service.name` and `service.version` | **Aligned** with the OpenTelemetry **service** resource namespace. Extra keys from `extra_attributes` are integrator-defined and MUST follow [SECURITY_REDACTION.md](SECURITY_REDACTION.md). |
| **Metric instrument names** | `replayt.workflow.run.outcomes_total`, `replayt.workflow.run.duration_ms`, `replayt.exporter.errors_total` | **Application-specific** names—not copied from the OpenTelemetry well-known metric catalog (HTTP, RPC, etc.). The `replayt.*` prefix and dotted logical names reserve a **stable integrator-facing** namespace and avoid collisions with platform metrics. |
| **Instrument units** | Counters use `1`; the duration histogram uses `ms` | **Consistent** with common OpenTelemetry usage for dimensionless counts and milliseconds. |
| **Meter instrumentation scope** | Implementation uses `get_meter("replayt.workflow")` | Identifies metrics as originating from this workflow adapter; treat the scope string like **§3.1** tracer scope—renaming it is disruptive for backends that group by scope. |

**Intentional deviation:** This package does **not** claim that `replayt.*` metric names map 1:1 to a current OpenTelemetry **stable** semantic convention for “workflow runs” or “LLM applications,” because upstream definitions still evolve and may not match replayt’s lifecycle. If maintainers adopt OTel-standard names later, that is an explicit, **migrated** change (semver and CHANGELOG per **§6.8**).

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

### 6.8 OpenTelemetry semantic conventions alignment (traces and lifecycle signals)

**Scope:** Root **workflow run** span, lifecycle **span events**, and **span attributes** defined in **§4** and **§6** (excluding integrator-supplied `attributes` except where noted).

| Signal class | Canonical names (defaults) | Convention alignment |
| ------------ | ------------------------- | -------------------- |
| **Default span name** | `replayt.workflow.run` | **Application-specific.** Not aligned to OpenTelemetry Gen AI or RPC span naming: the run unit is defined by this adapter and the integrator’s boundary (**§2**, **§4**). Changing the default string is **semver-major** unless the previous default remains available as an alias (documented in [CHANGELOG.md](../CHANGELOG.md)). |
| **Span attributes** | `replayt.workflow.id`, `replayt.run.id`, `replayt.workflow.outcome`, `replayt.workflow.error.type`, `replayt.workflow.failure.category` | **Vendor-namespaced** keys under `replayt.*`. **Intentional deviation** from relying only on generic OTel attribute names for run identity and outcome: avoids collisions and reduces surprise when generic conventions change. |
| **Lifecycle span events** | `replayt.workflow.run.started`, `replayt.workflow.run.completed`, optional `replayt.workflow.milestone` (with `replayt.workflow.milestone.name` when used) | **Custom events.** Experimental OpenTelemetry Gen AI and other domain conventions target different span kinds (e.g. model/tool calls); they do **not** subsume these **run-level** lifecycle events. |
| **Tracer instrumentation scope** | Implementation resolves the tracer via `get_tracer(__name__)` → `replayt_opentelemetry_exporter.tracing` | Same **stability expectations** as **§3.1**. |

**Exception telemetry:** Calling `record_exception` on the span uses the standard OpenTelemetry span API; SDKs may attach stack traces to the exception event. Lifecycle **span attributes** and **event attributes** in **§6** remain subject to **§6.5** (no raw exception message in those fields). That split is **intentional**: operators get safe faceting on attributes while retaining SDK-level exception detail where backends show it.

**When upstream conventions evolve:** Names in **§5–§6**, **§5.7**, and this section are part of the **integrator contract**. Aligning with a future OpenTelemetry stable convention is **not automatic**—maintainers decide in a dedicated change with migration notes so dashboards and alerts do not break silently.

## 7. Version and compatibility expectations

**Compatibility matrix, pin justification, and CI validation policy** are specified in **[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md)**. This section stays the short normative snapshot for integrators; avoid duplicating matrix maintenance rules here.

### 7.1 Declared in `pyproject.toml` (normative ranges)

- **Python:** `requires-python` as specified in `[project]` (currently `>=3.11`).
- **OpenTelemetry:** `opentelemetry-api` and `opentelemetry-sdk` as in `[project.dependencies]` (currently `>=1.20.0,<2`). Integrators MAY use newer 1.x minors within that range. **OpenTelemetry Python 2.x** is **not supported** while the **`<2`** cap remains; adopting **2.x** is **Builder** work gated by [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7**—see **§7.4**.
- **replayt:** Lower bound as in `[project.dependencies]` (currently `>=0.4.0`). Upper bounds or caps MAY be added for known breakages.

### 7.2 Tested / documented matrix (maintenance obligation)

- CI job **`.github/workflows/ci.yml`** **`test`** runs the replayt×OpenTelemetry **four-cell** matrix on **Python 3.11** and **3.12** (see [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1**): replayt **0.4.0** and **latest**, OpenTelemetry API/SDK **1.20.0** and **1.40.0**, with resolved versions printed each cell (**requires-python parity** on the merge gate).
- **Mission Control baseline (phase 1c):** replayt **0.4.25** was installed when the backlog pipeline last captured dependency output; treat that as the **reference** public API snapshot for examples (`Workflow`, `Runner`, `RunContext`, `run_with_mock`, etc.) until README and the compatibility matrix claim a different line.
- **Deep snapshot:** **`docs/reference-documentation/`** holds version-stamped notes for those symbols aligned to matrix pins ([REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md)); integrators should still treat [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§2** as the normative seam for *this* package.
- When this repository claims support for a specific replayt line in README or [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md), update examples and §2.2 in the same release branch—**no TODO** for touchpoints once that version is advertised.

### 7.3 Compatibility snapshot (copy for releases)

Values below mirror `[project]` / `[project.dependencies]` in `pyproject.toml` at spec time; **maintainers update this table** when bounds change. **Version bump procedure**, **tag naming**, **CHANGELOG** cut lines, and **PyPI** publish steps are normative in **[RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md)** (keep **§7.3** aligned with **`[project].version`** when releasing).

| Component | Declared bound | Notes |
| --------- | ---------------- | ----- |
| Python | `requires-python` (currently `>=3.11`) | **Declared** floor **3.11**. **Merge gate:** full four-cell matrix on **3.11** and **3.12** ([COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1**). |
| OpenTelemetry API/SDK | `>=1.20.0,<2` | **1.x** supported within this range. **2.x** stays **out of scope** until [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7** is satisfied (**§7.2** spike or audit, **§7.3** outcomes, **§7.4** before new CI cells). |
| replayt | `>=0.4.0` | Upper cap **TODO** until a known-breaking replayt release is identified and tested. |
| Tested replayt (CI) | Matrix cells **0.4.0** and **latest** | See [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1**. |
| Reference replayt (examples) | **0.4.25** (baseline log) | Update when README claims a different line. |

### 7.4 OpenTelemetry 2.x policy (normative)

- **While `pyproject.toml` declares `<2`:** This package **does not** support installing alongside **OpenTelemetry Python API/SDK 2.x**. Integrators MUST stay on **1.x** versions that satisfy the declared lower bound.
- **Current Builder outcome:** [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7.2** records a **2026-03-29** PyPI audit: **no** published **2.x** for **`opentelemetry-api`** or **`opentelemetry-sdk`** (including pre-releases in the index at that check). Support for **2.x** stays **out of scope** until those packages exist and maintainers complete the full spike there (**§7.2** steps **1–3**) plus **§7.3–7.4** in that document for a *support* merge.
- **To support 2.x:** Maintainers follow [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7**—spike on a branch, then either widen bounds and expand CI per that section **or** document an explicit continued exclusion with rationale.
- **Optional OTLP extra:** Any **2.x** support claim MUST include aligned bounds for `opentelemetry-exporter-otlp-proto-http` (same major line as API/SDK); see [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§3.4** and **§7.1**.

### 7.5 TODO allowed

- Exact **upper** bounds for replayt or OTel when upstream has not yet published a breaking release: MAY remain `TODO` in [CHANGELOG.md](../CHANGELOG.md), here, or [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) until validated—provided **§3** of that document still records rationale for existing lower bounds.

## 8. Acceptance criteria (for Builder / QA)

The **documentation** backlog (phase 2) is complete when §1.1 holds for every backlog row that maps here. The **implementation** backlog (phase 3 onward) is complete when all of the following are true:

1. **Public API listed** — README links to this document and shows a minimal end-to-end example consistent with §3.3.
2. **`__all__` matches §3** — Every symbol named in the §3 table appears in package `__all__`.
3. **Run boundaries** — Behavior matches §4 (success path, error path with re-raise, span ended, metrics recorded per §4.1.1).
4. **Lifecycle traces** — `workflow_run_span` emits the **§6** lifecycle events (`replayt.workflow.run.started`, `replayt.workflow.run.completed`) and sets **§6** completion span attributes on success and failure paths; failure path keeps OTel ERROR status with a **safe** description (exception type only) and sets **`replayt.workflow.failure.category`** per **§6.4** (`unknown` when no mapping applies).
5. **Versions** — README and §7 state dependency ranges from `pyproject.toml` and the tested/reference replayt line per §7.2–7.3; [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§6** (compatibility matrix backlog) is satisfied for tables, justified bounds, and documented CI validation.
6. **Tests** — Pytest passes without merge artifacts; obligations in **[TESTING_SPEC.md](TESTING_SPEC.md)** **§4–§5** are met (success path, failure path, exporter-error path, fakes/determinism, replayt public surface only). Span attributes, lifecycle events/attributes per §6, success/failure metrics, `__all__` parity, and provider installation remain covered as today’s `tests/test_tracing.py` / `tests/test_pyproject_dependencies.py` demonstrate—extend or split modules when scenarios grow.
7. **Docs consistency** — README metric names, trace verification notes, and descriptions align with §5–§6, the **dated** [CHANGELOG.md](../CHANGELOG.md) section for the current **`[project].version`**, and **Unreleased** entries for work merged but not yet released (see [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) **§9**).
8. **CI readability** — [CI_SPEC.md](CI_SPEC.md) **§5** is satisfied: Ruff lint, Ruff format check, and pytest run in separately identifiable steps; failures surface the failing tool; exit codes are not masked; logs follow **§3.3–§3.4**; README satisfies **§3.5**.
9. **Operator monitoring** — [OPERATOR_MONITORING_SPEC.md](OPERATOR_MONITORING_SPEC.md) is satisfied: **`docs/OPERATOR_RUNBOOK.md`** exists (or README carries equivalent depth per that spec), links from README **Metrics** / **Operator monitoring**, and contains the §4–§7 content obligations (PromQL examples, Grafana panel intent, alert starting points) aligned with §5–§6.
10. **Replayt reference docs** — [REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md) is satisfied: **`docs/reference-documentation/README.md`** indexes version-stamped snapshots for **Workflow**, **Runner**, **RunContext**, and **run_with_mock** per matrix replayt pins; README and **REPLAYT_ECOSYSTEM_IDEA.md** link per that spec **§5**.
11. **Runner-based integration example** — **§3.4** is satisfied: **`docs/examples/runner_workflow_run_span.md`** exists, meets **§2.2.1** / **§3.4** content and public-API rules, has **§3.4** runnability via script **or** pytest per [TESTING_SPEC.md](TESTING_SPEC.md) **§4.2**, and README links to the markdown as required there.
12. **OpenTelemetry 2.x** — [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7** is satisfied: **§7.2** either full spike (**steps 1–3**) when **2.x** is on PyPI **or** step **0** PyPI audit recorded when **2.x** is absent; **§7.3** documentation outcome for **support** (bounds, matrix, README, CHANGELOG, **§7** here including **§7.3** snapshot) **or** **exclusion** (rationale recorded, this document **§7.4** and README accurate); if **support**: CI matrix meets that document **§7.4** and **full pytest** passes on at least one **2.x** cell; **`tests/test_pyproject_dependencies.py`** (or successor) matches declared bounds; optional **`[otlp]`** pins align with API/SDK.
13. **Release engineering** — [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) **§7** is satisfied: one **§6.1** version strategy, README **Releases** entry, **tag-gated** publish workflow with **trusted publishing**, documented **`build` + `twine check`**, **CHANGELOG** alignment (**§6.3**), and a **§6.4** drift guardrail (or documented waiver).
14. **Python 3.11 requires-python parity** — [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1** and [CI_SPEC.md](CI_SPEC.md) **§3.6**: merge gate runs the **full** replayt×OpenTelemetry matrix on **3.11** and **3.12**; Ruff + pytest match **§3.1** and README on every row; **§7.2**–**§7.3** here and README **Version compatibility** stay aligned (**declared vs tested**).
15. **Semantic conventions inventory** — **§5.7** and **§6.8** stay accurate for shipped metrics, resource attributes, span names, lifecycle events, and span attribute keys; any rename or new canonical identifier updates **§5–§6**, **§5.7**, **§6.8**, [OPERATOR_MONITORING_SPEC.md](OPERATOR_MONITORING_SPEC.md) when PromQL examples are affected, README **Metrics** / trace verification when user-facing, tests per [TESTING_SPEC.md](TESTING_SPEC.md) **§5**, and [CHANGELOG.md](../CHANGELOG.md) per the stability rules in **§6.8**.
16. **Changelog and milestone hygiene** — [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) **§9** is satisfied for the release line in scope: CHANGELOG **cut** and **compare** expectations (**§9.2.1–§9.2.2**), README vs shipped tracing/metrics (**§9.2.3**), **Upgrading** / adoption notes from **0.1.0** and any renames (**§9.2.4**), version consistency (**§9.2** item **5**), and milestone policy (**§9.3**) when applicable. **Evidence for 0.2.0:** **[CHANGELOG.md](../CHANGELOG.md)** `[0.2.0]` includes the GitHub compare link and **Upgrading from 0.1.0**; README **Releases and PyPI** states milestones are unused (**§9.3** N/A); README **Metrics** / tracing steps match **§5–§6** and `src/replayt_opentelemetry_exporter/tracing.py` at **`[project].version` 0.2.0** (Builder phase 3, backlog *Changelog and milestone hygiene for 0.2.0*).

## 9. Related documents

- [MISSION.md](MISSION.md) — Scope and audiences.
- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) — Narrow APIs and consumer-side maintenance.
- [TESTING_SPEC.md](TESTING_SPEC.md) — pytest strategy, replayt boundary tests, exporter error coverage, CI parity.
- [CI_SPEC.md](CI_SPEC.md) — Ruff + pytest CI steps, failure surfacing, safe logs.
- [RUN_SUMMARY_SPEC.md](RUN_SUMMARY_SPEC.md) — `RunSummary` / `generate_run_summary`.
- [SECURITY_REDACTION.md](SECURITY_REDACTION.md) — What MUST NOT appear in attributes or summaries; lifecycle defaults (**§6**).
- [OPERATOR_MONITORING_SPEC.md](OPERATOR_MONITORING_SPEC.md) — Dashboards, PromQL/Grafana recipes, and alert starting points for §5 metrics (runbook deliverable).
- [REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md) — Bounded local snapshot of replayt workflow/run public API under **`docs/reference-documentation/`**.
- [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7** — OpenTelemetry 2.x spike, policy, and CI gating (companion to **§7.4** here).
- [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) — PyPI publish, version single source of truth, tag-gated trusted publishing, **CHANGELOG** alignment (this document **§8** item **13**), **§9** changelog/README/milestone hygiene (this document **§8** item **16**).
- [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) — informative upstream reference; **§5.7** and **§6.8** document how this package relates to them.
