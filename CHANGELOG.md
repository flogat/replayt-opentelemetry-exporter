# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Phase **3** builder (*Add compatibility matrix and dependency pins for replayt and OpenTelemetry*): [`.github/workflows/ci.yml`](.github/workflows/ci.yml) job **`test`** runs a **four-cell** `strategy.matrix` on Python 3.12 (replayt **0.4.0** and **latest** × OpenTelemetry API/SDK **1.20.0** and **1.40.0**), reinstalls pins after the editable install, and logs resolved **`replayt`**, **`opentelemetry-api`**, and **`opentelemetry-sdk`** versions before Ruff and pytest. Runtime deps: **`replayt>=0.4.0`** (failure-category mapping uses replayt types covered from that line); **`opentelemetry-api`** / **`opentelemetry-sdk`** and optional OTLP exporter **`>=1.20.0,<2`** until OpenTelemetry 2.x is validated and documented. README **Version compatibility**, [docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) **§4–§5**, and [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §7 match the new bounds and matrix.
- `workflow_run_span` emits [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§6** lifecycle span events (`replayt.workflow.run.started`, `replayt.workflow.run.completed`) and sets completion attributes (`replayt.workflow.outcome`; on failure also `replayt.workflow.error.type` and `replayt.workflow.failure.category` with a documented exception-to-category map in `tracing.py`).
- `record_exporter_error` maps `error_type` to the recommended set in [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§5.3** (`export_failed`, `serialization_error`, `timeout`, `unknown`). Any other value is recorded as `unknown` so metric cardinality stays bounded; a debug log line notes the original value.
- `workflow_run_span` optional `attributes` are validated for export: blocked keys (credentials-style names per [docs/SECURITY_REDACTION.md](docs/SECURITY_REDACTION.md)) are omitted; long string values truncate at 100 characters; `replayt.workflow.id` / `replayt.run.id` cannot be overridden via the `attributes` dict.
- `build_meter_provider` and `install_meter_provider` accept optional `metric_readers` (for example `InMemoryMetricReader` in unit tests) in addition to `metric_exporters`, consistent with OpenTelemetry Python SDK types.

### Added
- Phase **3** builder (*Implement automated tests for replayt boundary and exporter behavior*): contract-style tests in **`tests/test_tracing.py`** run **`replayt.run_with_mock`** inside **`workflow_run_span`** using an in-memory **`EventStore`**-shaped store (no `replayt.persistence` imports), covering a successful terminal workflow and a failed run re-raised as **`RunFailed`** (failure category **runtime**). See [docs/TESTING_SPEC.md](docs/TESTING_SPEC.md) **§4.2**.
- Pytest module **`tests/test_pyproject_dependencies.py`** checks that installed wheels satisfy **`pyproject.toml`** runtime requirements and that OpenTelemetry specifiers stay below **2.0**.
- Phase **3** builder (*Define public exporter API and replayt integration seam*): pytest asserts success-path spans use status OK, error-path spans finish with an end time after re-raise, and `replayt_opentelemetry_exporter.__all__` matches [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §3.
- Counter metric `replayt.workflow.run.outcomes_total` (labels: `outcome`="success|failure", `workflow_id`) to track completed and failed workflow runs.
- Histogram metric `replayt.workflow.run.duration_ms` (labels: `outcome`, `workflow_id`) to track run durations.
- Counter metric `replayt.exporter.errors_total` (labels: `error_type`, optional `workflow_id` / `run_id`) to track exporter health and export-path failures.
- Metric cardinality kept low: `workflow_id` (operator guidance: tens to low hundreds per deployment), `outcome` (2 values), `error_type` (§5.3 recommended set; see **Changed** for normalization).

### Documentation
- Phase **5** architect (*Implement automated tests for replayt boundary and exporter behavior*): [docs/TESTING_SPEC.md](docs/TESTING_SPEC.md) **§2** backlog acceptance table now references **§4.3–§4.5** for success, failure, and exporter-error obligations (same numbering as **§4**).
- Phase **2** spec (*Implement automated tests for replayt boundary and exporter behavior*): [docs/TESTING_SPEC.md](docs/TESTING_SPEC.md) defines normative **pytest** usage, **CI parity** with [`.github/workflows/ci.yml`](.github/workflows/ci.yml), **exit codes**, in-memory OTel fakes, **success / failure / exporter-error** minimum scenarios, **contract-style** replayt boundary rules (public API only), and a **Builder checklist**; [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§1.1** maps the backlog here and **§8** item **6** references the testing spec; [docs/MISSION.md](docs/MISSION.md) **Aligned docs** includes **TESTING_SPEC**; README links the contract and documents pytest exit codes in **Running tests and lint locally**.
- Phase **2** spec (*Add compatibility matrix and dependency pins for replayt and OpenTelemetry*): [docs/COMPATIBILITY_MATRIX_SPEC.md](docs/COMPATIBILITY_MATRIX_SPEC.md) defines the normative **compatibility table** shape, **`pyproject.toml` justification** rules for replayt and OpenTelemetry, **CI matrix** obligations (vs current single-job resolver), and Spec vs Builder acceptance criteria; [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §1.1 maps the backlog here, §7 cross-links, §8 extends Builder checklist; README **Version compatibility** includes a snapshot table and points to the spec; [docs/DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md) references the matrix spec under **Explicit contracts**.
- Phase **2** spec (*Emit traces for replayt workflow run lifecycle with human-readable status*): [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§6** defines normative lifecycle span **events** (`replayt.workflow.run.started`, `replayt.workflow.run.completed`, optional `replayt.workflow.milestone`), completion **attributes** (`replayt.workflow.outcome`, `replayt.workflow.error.type`, `replayt.workflow.failure.category`), failure bucketing, cardinality/dashboard guidance, and Builder acceptance criteria; **§1.1** maps this backlog to the spec; [docs/SECURITY_REDACTION.md](docs/SECURITY_REDACTION.md) documents lifecycle defaults under the redaction policy; README verification step references **§6**.
- [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §5.1–§5.6: metric instruments, attribute summary, `error_type` values and normalization behavior, cardinality, advanced recording APIs, exemplar policy. README **Metrics** states how non-recommended `error_type` strings map to `unknown`.
- Added [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) specifying the stable public API (`__all__`), replayt integration seam, `workflow_run_span` run-boundary behavior, canonical metric instrument names, version expectations, and Builder acceptance criteria. README now links to the spec; the **Metrics** section matches that document.
- Phase **2** spec pass: backlog acceptance mapping (§1.1), normative `workflow_run_span` signature and ordered lifecycle, `get_workflow_tracer` instrumentation-scope rules, compatibility snapshot table (with replayt **0.4.25** baseline reference), README **Public surface at a glance** and **Version compatibility**.
- Phase **5** architect (*Define public exporter API and replayt integration seam*): architecture review; MISSION **Aligned docs** now includes **[PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md)** with the other pillar docs.
- Phase **5** architect (*Add compatibility matrix and dependency pins for replayt and OpenTelemetry*): [CHANGELOG.md](CHANGELOG.md) **Unreleased** groups **Changed**, **Added**, and **Documentation** without duplicate headings; [docs/MISSION.md](docs/MISSION.md) **Aligned docs** lists **[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md)** with the other pillar docs.

### Fixed
- **Phase 6 (security):** `workflow_run_span` sets span ERROR status to the exception **type name** only (not full `str(exc)`), matching [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §4.1 and reducing leakage via trace UIs. OpenTelemetry’s default `record_exception` / `set_status_on_exception` behavior on the run span is disabled so the status is not overwritten when the context manager re-raises.
- Resolved merge conflicts in `tracing.py` and `tests/test_tracing.py`. `workflow_run_span` uses `start_as_current_span` so spans end correctly on success and error paths (still re-raising after metrics and span error recording).
- Metric instruments now use the canonical names from the public spec: `replayt.workflow.run.outcomes_total`, `replayt.workflow.run.duration_ms`, and `replayt.exporter.errors_total`.

## [0.1.0] - 2026-03-25

### Added
- Initial scaffold and package layout.
