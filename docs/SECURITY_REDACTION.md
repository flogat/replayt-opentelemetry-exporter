# Security Redaction Policy for Spans and Metrics

This document defines the redaction and safe defaults for attributes in OpenTelemetry traces (spans) and metrics emitted by the replayt OpenTelemetry exporter.

**See also:** [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) for LLM/demos section on telemetry redaction and overall design principles.

## Categories

### Never Emit
The following categories of data MUST NEVER appear in span or metric attributes:
- Credentials (API keys, tokens, passwords)
- Personal Identifiable Information (PII) such as names, email addresses, phone numbers
- Secrets or sensitive configuration values
- Raw user input that may contain sensitive data
- **LLM-specific fields**: Raw prompts, completions, model inputs/outputs, or any content that could contain sensitive user data or proprietary model information

### Hash/Truncate
The following categories SHOULD be hashed or truncated to prevent leakage while preserving utility:
- Identifiers that are not public (e.g., internal IDs) - hash with a consistent algorithm
- Long strings that may contain sensitive data - truncate to a fixed length (e.g., 100 characters)
- Free-form text fields - hash or truncate to prevent PII leakage
- **LLM-specific fields**: Truncated prompts or completions (e.g., first 100 characters) for debugging purposes, with full content never stored

### Safe to Emit
The following categories are generally safe to emit:
- Public identifiers (e.g., workflow IDs, run IDs as defined in the tracing module)
- Standard OpenTelemetry semantic convention attributes
- Aggregated metrics (counts, durations) without raw values
- Status codes and error types (without sensitive error messages)
- **LLM-specific fields**: Model names, token counts, latency metrics, error types (without sensitive details)

## LLM-Specific Considerations

When working with LLM workflows, additional redaction rules apply (see [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) for LLM/demos section):
- **Never emit**: Raw prompts, completions, model inputs/outputs, or any content that could reveal proprietary model behavior or sensitive user data
- **Safe to emit**: Model identifiers (e.g., "gpt-4"), token counts, latency measurements, and high-level error categories
- **Hash/Truncate**: If debugging requires partial content visibility, truncate to a fixed length (e.g., first 100 characters) and hash the remainder

## Span status on errors (`workflow_run_span`)

On failure, the span’s **status description** is the exception’s **type name** (for example `ValueError`), not the full exception message, so arbitrary error text is not promoted to a first-class status field. A standard OpenTelemetry **exception** event is still recorded (which may include message and stack trace per the SDK); integrators should treat that like other sensitive telemetry and configure backends and retention accordingly.

## Lifecycle attributes and events (workflow run)

[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§6** defines **default** lifecycle signals: span attributes such as `replayt.workflow.outcome`, `replayt.workflow.error.type`, and `replayt.workflow.failure.category`, plus span **events** (`replayt.workflow.run.started`, `replayt.workflow.run.completed`, `replayt.workflow.milestone`). These defaults fall under **Safe to emit** when they use only the **documented** keys and **normalized** values (low-cardinality tokens, exception **type names**, not `str(exception)`). They MUST NOT carry raw prompts, credentials, PII, or unbounded free text. Optional integrator-supplied span attributes still pass through the `workflow_run_span(..., attributes={...})` filter described below.

## Optional span attributes (`workflow_run_span`)

Extra string attributes passed as `workflow_run_span(..., attributes={...})` are filtered in code: keys that match the **Never emit** patterns (for example `api_key`, names ending in `_token`, or containing `password`) are dropped; remaining string values longer than **100** characters are truncated. Canonical keys `replayt.workflow.id` and `replayt.run.id` come only from the `workflow_id` and `run_id` parameters so callers cannot override them via `attributes`.

## OpenTelemetry Semantic Conventions

When emitting attributes, follow OpenTelemetry semantic conventions where applicable:
- Use `service.name` for the service name (already implemented in `build_resource`)
- Use standard span names and attributes for workflow runs (e.g., `replayt.workflow.id`, `replayt.run.id`)
- Reference [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/) for standard attributes

## Run Summary Artifact

The `RunSummary` dataclass in `tracing.py` provides a PM- and support-facing summary artifact that excludes secret-bearing fields. It includes:
- Workflow and run identifiers (public)
- Timestamps (ISO 8601)
- Outcome (e.g., "success", "failure")
- High-level steps (list of step names)
- Duration in milliseconds
- Safe error messages (truncated to 100 characters)

All fields in `RunSummary` are non-secret and follow the redaction policy. The `generate_run_summary` function ensures that error messages are truncated and no sensitive data is included.

Example output (JSON):
