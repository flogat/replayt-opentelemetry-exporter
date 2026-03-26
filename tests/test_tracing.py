<<<<<<< HEAD
from __future__ import annotations
=======
from unittest.mock import patch
from datetime import datetime
>>>>>>> main

import pytest
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export import InMemorySpanExporter
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.trace import Tracer

from replayt_opentelemetry_exporter.tracing import (
    build_resource,
    build_tracer_provider,
    build_meter_provider,
    install_tracer_provider,
    install_meter_provider,
    get_workflow_tracer,
    workflow_run_span,
<<<<<<< HEAD
    _validate_attributes,
    record_run_outcome,
    record_exporter_error,
=======
    generate_run_summary,
    RunSummary,
>>>>>>> main
)


def test_build_resource_sets_service_name() -> None:
    resource = build_resource(service_name="test-service")
    assert resource.attributes["service.name"] == "test-service"


def test_build_resource_merges_extra_attributes() -> None:
    resource = build_resource(extra_attributes={"key": "value"})
    assert resource.attributes["key"] == "value"


def test_build_tracer_provider_records_spans() -> None:
    exporter = InMemorySpanExporter()
    provider = build_tracer_provider(span_exporters=[exporter])
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("test-span"):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "test-span"


def test_build_meter_provider_records_metrics() -> None:
    reader = InMemoryMetricReader()
    exporter = reader  # InMemoryMetricReader is also a MetricExporter
    provider = build_meter_provider(metric_exporters=[exporter])
    meter = provider.get_meter("test")
    counter = meter.create_counter("test-counter")
    counter.add(1)
    # Force collection
    reader.collect()
    metrics_data = reader.get_metrics_data()
    assert len(metrics_data.resource_metrics) > 0


def test_install_tracer_provider_calls_set_tracer_provider() -> None:
    exporter = InMemorySpanExporter()
    def capture_set(provider: TracerProvider) -> None:
        capture_set.called = True
        capture_set.provider = provider
    capture_set.called = False
    original_set = trace.set_tracer_provider
    trace.set_tracer_provider = capture_set
    try:
        result = install_tracer_provider(span_exporters=[exporter])
        assert capture_set.called
        assert capture_set.provider is result
    finally:
        trace.set_tracer_provider = original_set


def test_install_meter_provider_calls_set_meter_provider() -> None:
    reader = InMemoryMetricReader()
    def capture_set(provider: MeterProvider) -> None:
        capture_set.called = True
        capture_set.provider = provider
    capture_set.called = False
    original_set = metrics.set_meter_provider
    metrics.set_meter_provider = capture_set
    try:
        result = install_meter_provider(metric_exporters=[reader])
        assert capture_set.called
        assert capture_set.provider is result
    finally:
        metrics.set_meter_provider = original_set


def _workflow_tracer_from_memory_exporter() -> tuple[Tracer, InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = build_tracer_provider(span_exporters=[exporter])
    tracer = provider.get_tracer("test")
    return tracer, exporter


def test_workflow_run_span_sets_attributes() -> None:
    tracer, exporter = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-123", run_id="run-456"):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].attributes["replayt.workflow.id"] == "wf-123"
    assert spans[0].attributes["replayt.run.id"] == "run-456"


def test_workflow_run_span_omits_run_id_when_none() -> None:
    tracer, exporter = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-123"):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert "replayt.run.id" not in spans[0].attributes


def test_get_workflow_tracer_uses_global_provider() -> None:
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    tracer = get_workflow_tracer()
    assert tracer is not None


def test_workflow_run_span_records_success_metrics() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_exporters=[reader])
    metrics.set_meter_provider(provider)
    
    tracer, _ = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-123", run_id="run-456"):
        pass
<<<<<<< HEAD
    
    # Force collection
    reader.collect()
    metrics_data = reader.get_metrics_data()
    
    # Check that run counter was recorded
    found_run_counter = False
    for rm in metrics_data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "replayt.workflow.runs":
                    found_run_counter = True
                    # Check data points
                    for data_point in metric.data.data_points:
                        assert data_point.attributes.get("outcome") == "success"
                        assert data_point.attributes.get("workflow_id") == "wf-123"
                        assert data_point.value == 1
    assert found_run_counter, "replayt.workflow.runs metric not found"


def test_workflow_run_span_records_failure_metrics() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_exporters=[reader])
    metrics.set_meter_provider(provider)
    
    tracer, _ = _workflow_tracer_from_memory_exporter()
    try:
        with workflow_run_span(tracer, "wf-123", run_id="run-456"):
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Force collection
    reader.collect()
    metrics_data = reader.get_metrics_data()
    
    # Check that run counter was recorded with failure
    found_run_counter = False
    for rm in metrics_data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "replayt.workflow.runs":
                    found_run_counter = True
                    # Check data points
                    for data_point in metric.data.data_points:
                        if data_point.attributes.get("outcome") == "failure":
                            assert data_point.attributes.get("workflow_id") == "wf-123"
                            assert data_point.value == 1
    assert found_run_counter, "replayt.workflow.runs metric not found"


def test_record_exporter_error() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_exporters=[reader])
    metrics.set_meter_provider(provider)
    
    record_exporter_error("test_error", workflow_id="wf-123", run_id="run-456")
    
    # Force collection
    reader.collect()
    metrics_data = reader.get_metrics_data()
    
    # Check that error counter was recorded
    found_error_counter = False
    for rm in metrics_data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "replayt.exporter.errors":
                    found_error_counter = True
                    # Check data points
                    for data_point in metric.data.data_points:
                        assert data_point.attributes.get("error_type") == "test_error"
                        assert data_point.attributes.get("workflow_id") == "wf-123"
                        assert data_point.value == 1
    assert found_error_counter, "replayt.exporter.errors metric not found"


def test_duration_histogram_records_values() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_exporters=[reader])
    metrics.set_meter_provider(provider)
    
    tracer, _ = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-123", run_id="run-456"):
        pass
    
    # Force collection
    reader.collect()
    metrics_data = reader.get_metrics_data()
    
    # Check that duration histogram was recorded
    found_duration_histogram = False
    for rm in metrics_data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "replayt.workflow.duration":
                    found_duration_histogram = True
                    # Check data points
                    for data_point in metric.data.data_points:
                        assert data_point.attributes.get("workflow_id") == "wf-123"
                        assert data_point.count > 0
    assert found_duration_histogram, "replayt.workflow.duration metric not found"
=======
    names = [s.name for s in exporter.get_finished_spans()]
    assert "replayt.workflow.run" in names


def test_generate_run_summary_basic() -> None:
    """Test that generate_run_summary creates a RunSummary with safe fields."""
    tracer, exporter = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-summary", run_id="run-summary") as span:
        summary = generate_run_summary(
            span=span,
            workflow_id="wf-summary",
            run_id="run-summary",
            outcome="success",
            high_level_steps=["init", "process", "finalize"],
        )
    
    # Verify summary fields
    assert summary.workflow_id == "wf-summary"
    assert summary.run_id == "run-summary"
    assert summary.outcome == "success"
    assert summary.high_level_steps == ["init", "process", "finalize"]
    assert summary.duration_ms >= 0
    assert summary.error_message is None
    # Verify timestamps are ISO format
    datetime.fromisoformat(summary.start_time)
    datetime.fromisoformat(summary.end_time)


def test_generate_run_summary_with_error() -> None:
    """Test that error messages are truncated if too long."""
    tracer, exporter = _workflow_tracer_from_memory_exporter()
    long_error = "e" * 150  # Longer than 100 characters
    with workflow_run_span(tracer, "wf-error", run_id="run-error") as span:
        summary = generate_run_summary(
            span=span,
            workflow_id="wf-error",
            run_id="run-error",
            outcome="failure",
            high_level_steps=["init", "process"],
            error_message=long_error,
        )
    
    assert summary.outcome == "failure"
    assert summary.error_message is not None
    assert len(summary.error_message) == 103  # 100 + "..."
    assert summary.error_message.endswith("...")


def test_run_summary_dataclass_to_dict() -> None:
    """Test that RunSummary can be converted to dict for JSON export."""
    summary = RunSummary(
        workflow_id="wf-test",
        run_id="run-test",
        start_time="2024-01-01T00:00:00",
        end_time="2024-01-01T00:01:00",
        outcome="success",
        high_level_steps=["step1", "step2"],
        duration_ms=60000,
    )
    summary_dict = summary.__dict__
    assert summary_dict["workflow_id"] == "wf-test"
    assert summary_dict["outcome"] == "success"
    assert "password" not in str(summary_dict)  # Ensure no secrets in dict
>>>>>>> main
