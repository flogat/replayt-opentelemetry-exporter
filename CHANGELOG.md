# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation
- Added [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) specifying the stable public API (`__all__`), replayt integration seam, `workflow_run_span` run-boundary behavior, canonical metric instrument names, version expectations, and Builder acceptance criteria. README now links to the spec and aligns the metrics summary with that document.

### Added
- Counter metric `replayt.workflow.run.outcomes_total` (labels: `outcome`="success|failure", `workflow_id`) to track completed and failed workflow runs.
- Histogram metric `replayt.workflow.run.duration_ms` (labels: `outcome`, `workflow_id`) to track run durations.
- Counter metric `replayt.exporter.errors_total` (labels: `error_type`, `workflow_id`) to track exporter health and dropped events.
- Metric cardinality kept low: `workflow_id` (<100 distinct values expected per deployment), `outcome` (2 values), `error_type` (limited to enumerated types like "export_failed", "serialization_error", "timeout").

## [0.1.0] - 2026-03-25

### Added
- Initial scaffold and package layout.
