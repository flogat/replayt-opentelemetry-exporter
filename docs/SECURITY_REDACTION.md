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

## OpenTelemetry Semantic Conventions

When emitting attributes, follow OpenTelemetry semantic conventions where applicable:
- Use `service.name` for the service name (already implemented in `build_resource`)
- Use standard span names and attributes for workflow runs (e.g., `replayt.workflow.id`, `replayt.run.id`)
- Reference [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/) for standard attributes

## Implementation Notes

- The tracing module (`src/replayt_opentelemetry_exporter/tracing.py`) should validate attributes before emitting
- Tests should verify that sensitive attributes are not emitted
- This policy should be reviewed regularly and updated as needed

## References

- DESIGN_PRINCIPLES.md - LLM/demos section on telemetry redaction
- OpenTelemetry Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/
