from unittest.mock import patch

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Tracer

from replayt_opentelemetry_exporter import (
    build_resource,
    build_tracer_provider,
    build_meter_provider,
    get_workflow_tracer,
    install_tracer_provider,
    install_meter_provider,
    workflow_run_span,
    record_exporter_error,
)


def test_build_resource_sets_service_name() -> None:
    r = build_resource(service_name="my-replayt")
    assert r.attributes.get("service.name") == "my-replayt"


def test_build_resource_merges_extra_attributes() -> None:
    r = build_resource(extra_attributes={"deployment.environment": "dev"})
    assert r.attributes.get("deployment.environment") == "dev"


def test_build_tracer_provider_records_spans() -> None:
    resource = Resource.create({"service.name": "test"})
    exporter = InMemorySpanExporter()
    provider = build_tracer_provider(resource=resource, span_exporters=[exporter])
    tracer = provider.get_tracer("t")
    with tracer.start_as_current_span("s"):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "s"


def test_build_meter_provider_records_metrics() -> None:
    resource = Resource.create({"service.name": "test"})
    reader = InMemoryMetricReader()
    provider = build_meter_provider(resource=resource, metric_exporters=[reader])
    meter = provider.get_meter("t")
    counter = meter.create_counter("test_counter")
    counter.add(1)
    metrics_data = reader.get_metrics_data()
    assert len(metrics_data.resource_metrics) > 0


def test_install_tracer_provider_calls_set_tracer_provider() -> None:
    exporter = InMemorySpanExporter()
    captured: list[trace.TracerProvider] = []

    def capture_set(provider: TracerProvider) -> None:
        captured.append(provider)

    with patch.object(trace, "set_tracer_provider", side_effect=capture_set):
        out = install_tracer_provider(span_exporters=[exporter])
    assert len(captured) == 1
    assert captured[0] is out
    tracer = out.get_tracer("t")
    with tracer.start_as_current_span("s"):
        pass
    assert len(exporter.get_finished_spans()) == 1


def test_install_meter_provider_calls_set_meter_provider() -> None:
    reader = InMemoryMetricReader()
    captured: list[MeterProvider] = []

    def capture_set(provider: MeterProvider) -> None:
        captured.append(provider)

    with patch.object(metrics, "set_meter_provider", side_effect=capture_set):
        out = install_meter_provider(metric_exporters=[reader])
    assert len(captured) == 1
    assert captured[0] is out


def _workflow_tracer_from_memory_exporter() -> tuple[Tracer, InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = build_tracer_provider(span_exporters=[exporter])
    tracer = provider.get_tracer(
        "replayt_opentelemetry_exporter.workflow",
        "0.1.0",
    )
    return tracer, exporter


def test_workflow_run_span_sets_attributes() -> None:
    tracer, exporter = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-1", run_id="run-9"):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "replayt.workflow.run"
    assert span.attributes is not None
    assert span.attributes.get("replayt.workflow.id") == "wf-1"
    assert span.attributes.get("replayt.run.id") == "run-9"


def test_workflow_run_span_omits_run_id_when_none() -> None:
    tracer, exporter = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-2"):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    attrs = spans[0].attributes or {}
    assert attrs.get("replayt.workflow.id") == "wf-2"
    assert "replayt.run.id" not in attrs


def test_get_workflow_tracer_uses_global_provider() -> None:
    exporter = InMemorySpanExporter()
    install_tracer_provider(span_exporters=[exporter])
    tracer = get_workflow_tracer()
    with workflow_run_span(tracer, "wf-global"):
        pass
    names = [s.name for s in exporter.get_finished_spans()]
    assert "replayt.workflow.run" in names


def test_workflow_run_span_records_success_metrics() -> None:
    """Test that successful workflow runs record metrics."""
    # Setup metrics with in-memory reader
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    
    # Reset tracing module metrics to ensure fresh initialization
    import replayt_opentelemetry_exporter.tracing as tracing_module
    tracing_module._meter = None
    tracing_module._workflow_runs_completed = None
    tracing_module._workflow_runs_failed = None
    tracing_module._exporter_errors = None
    tracing_module._workflow_run_duration = None
    
    tracer, _ = _workflow_tracer_from_memory_exporter()
    
    with workflow_run_span(tracer, "workflow-123", run_id="run-456"):
        pass
    
    # Check metrics
    metrics_data = reader.get_metrics_data()
    resource_metrics = metrics_data.resource_metrics
    
    # Find the completed runs counter
    completed_metric = None
    for rm in resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "replayt.workflow.runs.completed":
                    completed_metric = metric
                    break
    
    assert completed_metric is not None
    # Verify the metric has data points
    assert len(completed_metric.data) > 0


def test_workflow_run_span_records_failure_metrics() -> None:
    """Test that failed workflow runs record metrics."""
    # Setup metrics with in-memory reader
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    
    # Reset tracing module metrics to ensure fresh initialization
    import replayt_opentelemetry_exporter.tracing as tracing_module
    tracing_module._meter = None
    tracing_module._workflow_runs_completed = None
    tracing_module._workflow_runs_failed = None
    tracing_module._exporter_errors = None
    tracing_module._workflow_run_duration = None
    
    tracer, _ = _workflow_tracer_from_memory_exporter()
    
    try:
        with workflow_run_span(tracer, "workflow-123", run_id="run-456"):
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Check metrics
    metrics_data = reader.get_metrics_data()
    resource_metrics = metrics_data.resource_metrics
    
    # Find the failed runs counter
    failed_metric = None
    for rm in resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "replayt.workflow.runs.failed":
                    failed_metric = metric
                    break
    
    assert failed_metric is not None
    # Verify the metric has data points
    assert len(failed_metric.data) > 0


def test_record_exporter_error() -> None:
    """Test that exporter errors are recorded."""
    # Setup metrics with in-memory reader
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    
    # Reset tracing module metrics to ensure fresh initialization
    import replayt_opentelemetry_exporter.tracing as tracing_module
    tracing_module._meter = None
    tracing_module._workflow_runs_completed = None
    tracing_module._workflow_runs_failed = None
    tracing_module._exporter_errors = None
    tracing_module._workflow_run_duration = None
    
    # Record an exporter error
    record_exporter_error()
    
    # Check metrics
    metrics_data = reader.get_metrics_data()
    resource_metrics = metrics_data.resource_metrics
    
    # Find the exporter errors counter
    errors_metric = None
    for rm in resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "replayt.exporter.errors":
                    errors_metric = metric
                    break
    
    assert errors_metric is not None
    # Verify the metric has data points
    assert len(errors_metric.data) > 0


def test_duration_histogram_records_values() -> None:
    """Test that duration histogram records values."""
    # Setup metrics with in-memory reader
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    
    # Reset tracing module metrics to ensure fresh initialization
    import replayt_opentelemetry_exporter.tracing as tracing_module
    tracing_module._meter = None
    tracing_module._workflow_runs_completed = None
    tracing_module._workflow_runs_failed = None
    tracing_module._exporter_errors = None
    tracing_module._workflow_run_duration = None
    
    tracer, _ = _workflow_tracer_from_memory_exporter()
    
    with workflow_run_span(tracer, "workflow-123", run_id="run-456"):
        pass
    
    # Check metrics
    metrics_data = reader.get_metrics_data()
    resource_metrics = metrics_data.resource_metrics
    
    # Find the duration histogram
    duration_metric = None
    for rm in resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "replayt.workflow.run.duration":
                    duration_metric = metric
                    break
    
    assert duration_metric is not None
    # Verify the metric has data points
    assert len(duration_metric.data) > 0
