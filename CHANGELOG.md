# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- `workflow_run_span` optional `attributes` are validated for export: blocked keys (credentials-style names per [docs/SECURITY_REDACTION.md](docs/SECURITY_REDACTION.md)) are omitted; long string values truncate at 100 characters; `replayt.workflow.id` / `replayt.run.id` cannot be overridden via the `attributes` dict.
- `build_meter_provider` and `install_meter_provider` accept optional `metric_readers` (for example `InMemoryMetricReader` in unit tests) in addition to `metric_exporters`, consistent with OpenTelemetry Python SDK types.

### Documentation
- Added [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) specifying the stable public API (`__all__`), replayt integration seam, `workflow_run_span` run-boundary behavior, canonical metric instrument names, version expectations, and Builder acceptance criteria. README now links to the spec and aligns the metrics summary with that document.
- Phase **2** spec pass: backlog acceptance mapping (§1.1), normative `workflow_run_span` signature and ordered lifecycle, `get_workflow_tracer` instrumentation-scope rules, compatibility snapshot table (with replayt **0.4.25** baseline reference), README **Public surface at a glance** and **Version compatibility**.
- Phase **3** builder: CI logs resolved replayt version; spec §7.2–7.3 and README **Version compatibility** describe CI vs reference snapshot; SECURITY_REDACTION documents `workflow_run_span` attribute filtering.
- Phase **5** architect: PUBLIC_API_SPEC §4.1 success/failure wording aligned with §4.1.1 and `workflow_run_span` (metrics and re-raise while the span is still active; span ends on context exit).

### Fixed
- Resolved merge conflicts in `tracing.py` and `tests/test_tracing.py`. `workflow_run_span` uses `start_as_current_span` so spans end correctly on success and error paths (still re-raising after metrics and span error recording).
- Metric instruments now use the canonical names from the public spec: `replayt.workflow.run.outcomes_total`, `replayt.workflow.run.duration_ms`, and `replayt.exporter.errors_total`.

### Added
- Counter metric `replayt.workflow.run.outcomes_total` (labels: `outcome`="success|failure", `workflow_id`) to track completed and failed workflow runs.
- Histogram metric `replayt.workflow.run.duration_ms` (labels: `outcome`, `workflow_id`) to track run durations.
- Counter metric `replayt.exporter.errors_total` (labels: `error_type`, `workflow_id`) to track exporter health and dropped events.
- Metric cardinality kept low: `workflow_id` (<100 distinct values expected per deployment), `outcome` (2 values), `error_type` (limited to enumerated types like "export_failed", "serialization_error", "timeout").

## [0.1.0] - 2026-03-25

### Added
- Initial scaffold and package layout.
