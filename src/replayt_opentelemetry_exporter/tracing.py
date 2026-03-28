from __future__ import annotations

import logging
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

from opentelemetry import metrics, trace
from opentelemetry.metrics import Counter, Histogram, MeterProvider
from opentelemetry.sdk.metrics import MeterProvider as SdkMeterProvider
from opentelemetry.sdk.metrics.export import (
    MetricExporter,
    MetricReader,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.trace import Span, Tracer

logger = logging.getLogger(__name__)

# Span attribute keys reserved for workflow_id / run_id parameters (extras must not override).
_RESERVED_SPAN_ATTRIBUTE_KEYS = frozenset({"replayt.workflow.id", "replayt.run.id"})

_EXACT_BLOCKED_ATTRIBUTE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
        "authorization",
        "bearer",
        "cookie",
        "client_secret",
        "private_key",
        "prompt",
        "completion",
        "model_input",
        "model_output",
    }
)

_MAX_ATTRIBUTE_VALUE_LEN = 100

# Global metrics instruments
_run_counter: Counter | None = None
_error_counter: Counter | None = None
_duration_histogram: Histogram | None = None


def _package_version() -> str:
    try:
        from importlib.metadata import version

        return version("replayt-opentelemetry-exporter")
    except Exception:
        return "unknown"


def build_resource(
    *,
    service_name: str = "replayt",
    extra_attributes: dict[str, str] | None = None,
) -> Resource:
    attributes = {
        "service.name": service_name,
        "service.version": _package_version(),
    }
    if extra_attributes:
        attributes.update(extra_attributes)
    return Resource.create(attributes)


def build_tracer_provider(
    *,
    resource: Resource | None = None,
    span_exporters: Sequence[SpanExporter] | None = None,
    service_name: str = "replayt",
) -> TracerProvider:
    resource = resource or build_resource(service_name=service_name)
    tracer_provider = TracerProvider(resource=resource)
    if span_exporters:
        for exporter in span_exporters:
            processor = BatchSpanProcessor(exporter)
            tracer_provider.add_span_processor(processor)
    return tracer_provider


def build_meter_provider(
    *,
    resource: Resource | None = None,
    metric_exporters: Sequence[MetricExporter] | None = None,
    metric_readers: Sequence[MetricReader] | None = None,
    service_name: str = "replayt",
) -> MeterProvider:
    global _run_counter, _error_counter, _duration_histogram
    resource = resource or build_resource(service_name=service_name)
    readers: list[MetricReader] = []
    if metric_exporters:
        for exporter in metric_exporters:
            readers.append(PeriodicExportingMetricReader(exporter))
    if metric_readers:
        readers.extend(metric_readers)
    meter_provider = SdkMeterProvider(resource=resource, metric_readers=readers)

    meter = meter_provider.get_meter("replayt.workflow")
    _run_counter = meter.create_counter(
        "replayt.workflow.run.outcomes_total",
        description="Count of workflow runs by outcome",
        unit="1",
    )
    _error_counter = meter.create_counter(
        "replayt.exporter.errors_total",
        description="Count of exporter errors",
        unit="1",
    )
    _duration_histogram = meter.create_histogram(
        "replayt.workflow.run.duration_ms",
        description="Duration of workflow runs",
        unit="ms",
    )

    return meter_provider


def install_tracer_provider(
    *,
    resource: Resource | None = None,
    span_exporters: Sequence[SpanExporter] | None = None,
    service_name: str = "replayt",
) -> TracerProvider:
    tracer_provider = build_tracer_provider(
        resource=resource,
        span_exporters=span_exporters,
        service_name=service_name,
    )
    trace.set_tracer_provider(tracer_provider)
    return tracer_provider


def install_meter_provider(
    *,
    resource: Resource | None = None,
    metric_exporters: Sequence[MetricExporter] | None = None,
    metric_readers: Sequence[MetricReader] | None = None,
    service_name: str = "replayt",
) -> MeterProvider:
    meter_provider = build_meter_provider(
        resource=resource,
        metric_exporters=metric_exporters,
        metric_readers=metric_readers,
        service_name=service_name,
    )
    metrics.set_meter_provider(meter_provider)
    return meter_provider


def get_workflow_tracer() -> Tracer:
    tracer = trace.get_tracer(__name__)
    return tracer


def _key_blocked_for_redaction(key: str) -> bool:
    """Return True if the attribute key must not be emitted (SECURITY_REDACTION.md)."""
    k = key.lower()
    if k in _EXACT_BLOCKED_ATTRIBUTE_KEYS:
        return True
    if "password" in k or "passwd" in k:
        return True
    if "api_key" in k or "apikey" in k:
        return True
    if k.endswith("_token") or k.endswith("_secret"):
        return True
    return False


def _safe_span_status_description(exc: BaseException) -> str:
    """Short, non-message span status text (PUBLIC_API_SPEC §4.1; SECURITY_REDACTION)."""
    return type(exc).__name__


def _validate_attributes(attributes: dict[str, str]) -> dict[str, str]:
    """Drop blocked keys and truncate long string values per SECURITY_REDACTION.md."""
    out: dict[str, str] = {}
    for key, value in attributes.items():
        if key in _RESERVED_SPAN_ATTRIBUTE_KEYS:
            continue
        if _key_blocked_for_redaction(key):
            logger.debug("Omitted span attribute key %r (redaction policy)", key)
            continue
        if len(value) > _MAX_ATTRIBUTE_VALUE_LEN:
            out[key] = value[:_MAX_ATTRIBUTE_VALUE_LEN]
        else:
            out[key] = value
    return out


def record_run_outcome(
    success: bool,
    workflow_id: str,
    run_id: str | None = None,
    duration_ms: float | None = None,
) -> None:
    """Record workflow run outcome metrics."""
    outcome_label = "success" if success else "failure"
    if _run_counter is not None:
        attributes: dict[str, str] = {
            "workflow_id": workflow_id,
            "outcome": outcome_label,
        }
        if run_id:
            attributes["run_id"] = run_id
        _run_counter.add(1, attributes)

    if duration_ms is not None and _duration_histogram is not None:
        hist_attrs: dict[str, str] = {
            "workflow_id": workflow_id,
            "outcome": outcome_label,
        }
        if run_id:
            hist_attrs["run_id"] = run_id
        _duration_histogram.record(duration_ms, hist_attrs)


def record_exporter_error(
    error_type: str, workflow_id: str | None = None, run_id: str | None = None
) -> None:
    """Record exporter error metrics."""
    if _error_counter is not None:
        attributes: dict[str, str] = {
            "error_type": error_type,
        }
        if workflow_id:
            attributes["workflow_id"] = workflow_id
        if run_id:
            attributes["run_id"] = run_id
        _error_counter.add(1, attributes)


@dataclass
class RunSummary:
    """Summary of a replayt workflow run for PM and support-facing artifacts.

    This dataclass defines the safe fields that can be included in a run summary.
    All fields are non-secret and follow the security redaction policy.
    """

    workflow_id: str
    run_id: str
    start_time: str  # ISO 8601 timestamp
    end_time: str  # ISO 8601 timestamp
    outcome: str  # e.g., "success", "failure", "cancelled"
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
    start_time = datetime.fromtimestamp(span.start_time / 1e9).isoformat()
    end_time = (
        datetime.fromtimestamp(span.end_time / 1e9).isoformat() if span.end_time else start_time
    )

    duration_ms = int((span.end_time - span.start_time) / 1e6) if span.end_time else 0

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
    attributes: dict[str, str] | None = None,
) -> Iterator[Span]:
    start_time = time.time()
    # Disable OTel's default exception hook: it sets span status to f"{Type}: {exc}" on re-raise,
    # which leaks arbitrary exception text; we record the exception and set a safe status below.
    with tracer.start_as_current_span(
        span_name,
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        span.set_attribute("replayt.workflow.id", workflow_id)
        if run_id:
            span.set_attribute("replayt.run.id", run_id)
        if attributes:
            validated = _validate_attributes(attributes)
            for key, value in validated.items():
                span.set_attribute(key, value)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, _safe_span_status_description(e)))
            duration_ms = (time.time() - start_time) * 1000
            record_run_outcome(
                success=False,
                workflow_id=workflow_id,
                run_id=run_id,
                duration_ms=duration_ms,
            )
            raise
        else:
            span.set_status(trace.Status(trace.StatusCode.OK))
            duration_ms = (time.time() - start_time) * 1000
            record_run_outcome(
                success=True,
                workflow_id=workflow_id,
                run_id=run_id,
                duration_ms=duration_ms,
            )
