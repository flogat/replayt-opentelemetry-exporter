# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- `record_exporter_error` maps `error_type` to the recommended set in [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) **§5.3** (`export_failed`, `serialization_error`, `timeout`, `unknown`). Any other value is recorded as `unknown` so metric cardinality stays bounded; a debug log line notes the original value.
- `workflow_run_span` optional `attributes` are validated for export: blocked keys (credentials-style names per [docs/SECURITY_REDACTION.md](docs/SECURITY_REDACTION.md)) are omitted; long string values truncate at 100 characters; `replayt.workflow.id` / `replayt.run.id` cannot be overridden via the `attributes` dict.
- `build_meter_provider` and `install_meter_provider` accept optional `metric_readers` (for example `InMemoryMetricReader` in unit tests) in addition to `metric_exporters`, consistent with OpenTelemetry Python SDK types.

### Documentation
- [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §5.1–§5.6: metric instruments, attribute summary, `error_type` values and normalization behavior, cardinality, advanced recording APIs, exemplar policy. README **Metrics** states how non-recommended `error_type` strings map to `unknown`.
- Added [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) specifying the stable public API (`__all__`), replayt integration seam, `workflow_run_span` run-boundary behavior, canonical metric instrument names, version expectations, and Builder acceptance criteria. README now links to the spec and aligns the metrics summary with that document.
- Phase **2** spec pass: backlog acceptance mapping (§1.1), normative `workflow_run_span` signature and ordered lifecycle, `get_workflow_tracer` instrumentation-scope rules, compatibility snapshot table (with replayt **0.4.25** baseline reference), README **Public surface at a glance** and **Version compatibility**.
- Phase **3** builder: CI logs resolved replayt version; spec §7.2–7.3 and README **Version compatibility** describe CI vs reference snapshot; SECURITY_REDACTION documents `workflow_run_span` attribute filtering.
- Phase **5** architect (*Define public exporter API and replayt integration seam*): architecture review; MISSION **Aligned docs** now includes **[PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md)** with the other pillar docs.

### Fixed
- **Phase 6 (security):** `workflow_run_span` sets span ERROR status to the exception **type name** only (not full `str(exc)`), matching [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §4.1 and reducing leakage via trace UIs. OpenTelemetry’s default `record_exception` / `set_status_on_exception` behavior on the run span is disabled so the status is not overwritten when the context manager re-raises.
- Resolved merge conflicts in `tracing.py` and `tests/test_tracing.py`. `workflow_run_span` uses `start_as_current_span` so spans end correctly on success and error paths (still re-raising after metrics and span error recording).
- Metric instruments now use the canonical names from the public spec: `replayt.workflow.run.outcomes_total`, `replayt.workflow.run.duration_ms`, and `replayt.exporter.errors_total`.

### Added
- Phase **3** builder (*Define public exporter API and replayt integration seam*): pytest asserts success-path spans use status OK, error-path spans finish with an end time after re-raise, and `replayt_opentelemetry_exporter.__all__` matches [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §3.
- Counter metric `replayt.workflow.run.outcomes_total` (labels: `outcome`="success|failure", `workflow_id`) to track completed and failed workflow runs.
- Histogram metric `replayt.workflow.run.duration_ms` (labels: `outcome`, `workflow_id`) to track run durations.
- Counter metric `replayt.exporter.errors_total` (labels: `error_type`, optional `workflow_id` / `run_id`) to track exporter health and export-path failures.
- Metric cardinality kept low: `workflow_id` (operator guidance: tens to low hundreds per deployment), `outcome` (2 values), `error_type` (§5.3 recommended set; see **Changed** for normalization).

## [0.1.0] - 2026-03-25

### Added
- Initial scaffold and package layout.
