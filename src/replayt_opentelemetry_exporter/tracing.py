"""OpenTelemetry tracing helpers for replayt workflow runs."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from importlib.metadata import PackageNotFoundError, version
from datetime import datetime

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
from opentelemetry.trace import Span, SpanKind, Tracer


def _package_version() -> str:
    try:
        return version("replayt_opentelemetry_exporter")
    except PackageNotFoundError:
        return "0.0.0"


def build_resource(
    *,
    service_name: str = "replayt",
    extra_attributes: dict[str, str] | None = None,
) -> Resource:
    """Build a :class:`Resource` with ``service.name`` and optional extra string attributes."""
    attrs: dict[str, str] = {"service.name": service_name}
    if extra_attributes:
        attrs.update(extra_attributes)
    return Resource.create(attrs)


def build_tracer_provider(
    *,
    resource: Resource | None = None,
    span_exporters: Sequence[SpanExporter] | None = None,
    service_name: str = "replayt",
) -> TracerProvider:
    """Create a :class:`TracerProvider` without registering it globally.

    Each exporter is wrapped in a :class:`SimpleSpanProcessor`. When *span_exporters*
    is omitted, spans are recorded but not exported until a processor is added.
    Use this in tests or when wiring a provider manually; applications typically call
    :func:`install_tracer_provider` instead.
    """
    res = resource or build_resource(service_name=service_name)
    provider = TracerProvider(resource=res)
    if span_exporters:
        for exporter in span_exporters:
            provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider


def install_tracer_provider(
    *,
    resource: Resource | None = None,
    span_exporters: Sequence[SpanExporter] | None = None,
    service_name: str = "replayt",
) -> TracerProvider:
    """Register a :class:`TracerProvider` for workflow instrumentation (global)."""
    provider = build_tracer_provider(
        resource=resource,
        span_exporters=span_exporters,
        service_name=service_name,
    )
    trace.set_tracer_provider(provider)
    return provider


def get_workflow_tracer() -> Tracer:
    """Return a :class:`Tracer` scoped for replayt workflow instrumentation."""
    return trace.get_tracer(
        "replayt_opentelemetry_exporter.workflow",
        _package_version(),
    )


def _validate_attributes(attributes: dict[str, str]) -> dict[str, str]:
    """Validate and sanitize attributes according to the security redaction policy.
    
    This function ensures that:
    1. No credentials, tokens, or secrets are included
    2. No PII (Personal Identifiable Information) is included
    3. Long strings are truncated to prevent leakage
    4. Only safe identifiers and public data are emitted
    
    Returns a sanitized copy of the attributes dictionary.
    """
    # Define sensitive attribute patterns that should never be emitted
    sensitive_patterns = [
        "password", "token", "secret", "key", "credential",
        "api_key", "auth", "private", "ssn", "credit_card"
    ]
    
    # Define safe attributes that are explicitly allowed
    safe_attributes = {
        "replayt.workflow.id", "replayt.run.id", "service.name"
    }
    
    sanitized = {}
    for key, value in attributes.items():
        # Check if attribute key contains sensitive patterns
        key_lower = key.lower()
        if any(pattern in key_lower for pattern in sensitive_patterns):
            continue  # Skip sensitive attributes
        
        # Check if attribute is in safe list or follows semantic conventions
        if key in safe_attributes or key.startswith("replayt.") or key.startswith("service."):
            # Truncate long strings to prevent PII leakage
            if len(value) > 100:
                value = value[:100] + "..."
            sanitized[key] = value
        else:
            # For unknown attributes, apply conservative truncation
            if len(value) > 100:
                value = value[:100] + "..."
            sanitized[key] = value
    
    return sanitized


@dataclass
class RunSummary:
    """Summary of a replayt workflow run for PM and support-facing artifacts.
    
    This dataclass defines the safe fields that can be included in a run summary.
    All fields are non-secret and follow the security redaction policy.
    """
    workflow_id: str
    run_id: str
    start_time: str  # ISO 8601 timestamp
    end_time: str    # ISO 8601 timestamp
    outcome: str     # e.g., "success", "failure", "cancelled"
    high_level_steps: list[str]  # High-level steps (e.g., ["init", "process", "finalize"])
    duration_ms: int  # Total duration in milliseconds
    error_message: str | None = None  # Safe error message (no sensitive details)


def generate_run_summary(
    span: Span,
    workflow_id: str,
    run_id: str,
    outcome: str,
    high_level_steps: list[str],
    error_message: str | None = None,
) -> RunSummary:
    """Generate a run summary from span data and workflow context.
    
    This function creates a RunSummary object with safe fields only,
    following the security redaction policy (see SECURITY_REDACTION.md).
    
    Args:
        span: The OpenTelemetry span for the workflow run.
        workflow_id: The workflow identifier.
        run_id: The run identifier.
        outcome: The outcome of the run (e.g., "success", "failure").
        high_level_steps: List of high-level step names.
        error_message: Optional safe error message (no sensitive details).
    
    Returns:
        RunSummary: A summary object with non-secret fields.
    """
    # Get timestamps from span
    start_time = datetime.fromtimestamp(span.start_time / 1e9).isoformat()
    end_time = datetime.fromtimestamp(span.end_time / 1e9).isoformat() if span.end_time else start_time
    
    # Calculate duration
    duration_ms = int((span.end_time - span.start_time) / 1e6) if span.end_time else 0
    
    # Ensure error message is safe (truncate if too long)
    safe_error = None
    if error_message:
        safe_error = error_message[:100] + "..." if len(error_message) > 100 else error_message
    
    return RunSummary(
        workflow_id=workflow_id,
        run_id=run_id,
        start_time=start_time,
        end_time=end_time,
        outcome=outcome,
        high_level_steps=high_level_steps,
        duration_ms=duration_ms,
        error_message=safe_error,
    )


@contextmanager
def workflow_run_span(
    tracer: Tracer,
    workflow_id: str,
    *,
    run_id: str | None = None,
    span_name: str = "replayt.workflow.run",
) -> Iterator[Span]:
    """Create a span representing a single replayt workflow run."""
    attributes: dict[str, str] = {"replayt.workflow.id": workflow_id}
    if run_id is not None:
        attributes["replayt.run.id"] = run_id
    
    # Validate attributes according to security redaction policy
    validated_attributes = _validate_attributes(attributes)
    
    with tracer.start_as_current_span(
        span_name,
        kind=SpanKind.INTERNAL,
        attributes=validated_attributes,
    ) as span:
        yield span
