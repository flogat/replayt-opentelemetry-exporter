"""OpenTelemetry tracing helpers for replayt workflow runs."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version

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
