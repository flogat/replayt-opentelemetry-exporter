from __future__ import annotations

from datetime import datetime

import pytest
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import StatusCode, Tracer

import replayt_opentelemetry_exporter.tracing as tracing_mod
from replayt_opentelemetry_exporter.tracing import (
    RunSummary,
    build_meter_provider,
    build_resource,
    build_tracer_provider,
    generate_run_summary,
    get_workflow_tracer,
    install_meter_provider,
    install_tracer_provider,
    record_exporter_error,
    workflow_run_span,
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
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "test-span"


def test_build_meter_provider_records_metrics() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    meter = provider.get_meter("test")
    counter = meter.create_counter("test-counter")
    counter.add(1)
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
        result = install_meter_provider(metric_readers=[reader])
        assert capture_set.called
        assert capture_set.provider is result
    finally:
        metrics.set_meter_provider = original_set


def _workflow_tracer_from_memory_exporter() -> tuple[Tracer, InMemorySpanExporter, TracerProvider]:
    exporter = InMemorySpanExporter()
    provider = build_tracer_provider(span_exporters=[exporter])
    tracer = provider.get_tracer("test")
    return tracer, exporter, provider


def test_workflow_run_span_sets_attributes() -> None:
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-123", run_id="run-456"):
        pass
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "replayt.workflow.run"
    assert spans[0].attributes["replayt.workflow.id"] == "wf-123"
    assert spans[0].attributes["replayt.run.id"] == "run-456"


def test_workflow_run_span_omits_run_id_when_none() -> None:
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-123"):
        pass
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert "replayt.run.id" not in spans[0].attributes


def test_workflow_run_span_custom_span_name() -> None:
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-123", span_name="custom.run"):
        pass
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "custom.run"


def test_workflow_run_span_reraises_same_exception() -> None:
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with pytest.raises(ValueError, match="expected"):
        with workflow_run_span(tracer, "wf-123"):
            raise ValueError("expected")
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR


def test_workflow_run_span_merges_extra_attributes() -> None:
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(
        tracer,
        "wf-123",
        attributes={"custom.dim": "us-east-1"},
    ):
        pass
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert spans[0].attributes["custom.dim"] == "us-east-1"


def test_workflow_run_span_reserved_keys_in_attributes_do_not_override() -> None:
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(
        tracer,
        "wf-canonical",
        run_id="run-canonical",
        attributes={
            "replayt.workflow.id": "wf-evil",
            "replayt.run.id": "run-evil",
            "custom.dim": "ok",
        },
    ):
        pass
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert spans[0].attributes["replayt.workflow.id"] == "wf-canonical"
    assert spans[0].attributes["replayt.run.id"] == "run-canonical"
    assert spans[0].attributes["custom.dim"] == "ok"


def test_workflow_run_span_omits_blocked_attribute_keys() -> None:
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(
        tracer,
        "wf-123",
        attributes={"api_key": "secret-value", "region": "eu"},
    ):
        pass
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert "api_key" not in spans[0].attributes
    assert spans[0].attributes["region"] == "eu"


def test_workflow_run_span_truncates_long_attribute_values() -> None:
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    long_val = "x" * 150
    with workflow_run_span(tracer, "wf-123", attributes={"note": long_val}):
        pass
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert spans[0].attributes["note"] == "x" * 100


def test_get_workflow_tracer_uses_global_provider() -> None:
    previous = trace.get_tracer_provider()
    try:
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        tracer = get_workflow_tracer()
        assert tracer is not None
    finally:
        trace.set_tracer_provider(previous)


def _tracer_scope_name(tracer: Tracer) -> str:
    scope = getattr(tracer, "instrumentation_scope", None) or getattr(
        tracer, "_instrumentation_scope", None
    )
    assert scope is not None
    return scope.name


def test_get_workflow_tracer_uses_stable_instrumentation_scope_name() -> None:
    """Instrumentation scope string matches the tracing submodule (PUBLIC_API_SPEC §3.1)."""
    t1 = get_workflow_tracer()
    t2 = trace.get_tracer(tracing_mod.__name__)
    assert _tracer_scope_name(t1) == tracing_mod.__name__
    assert _tracer_scope_name(t2) == tracing_mod.__name__


def test_workflow_run_span_records_success_metrics() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(provider)
        tracer, _, trace_provider = _workflow_tracer_from_memory_exporter()
        with workflow_run_span(tracer, "wf-123", run_id="run-456"):
            pass
        trace_provider.force_flush()

        reader.collect()
        metrics_data = reader.get_metrics_data()

        found_run_counter = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.workflow.run.outcomes_total":
                        found_run_counter = True
                        for data_point in metric.data.data_points:
                            assert data_point.attributes.get("outcome") == "success"
                            assert data_point.attributes.get("workflow_id") == "wf-123"
                            assert data_point.value == 1
        assert found_run_counter, "replayt.workflow.run.outcomes_total metric not found"
    finally:
        metrics.set_meter_provider(previous_meter)


def test_workflow_run_span_records_failure_metrics() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(provider)
        tracer, _, trace_provider = _workflow_tracer_from_memory_exporter()
        try:
            with workflow_run_span(tracer, "wf-123", run_id="run-456"):
                raise ValueError("Test error")
        except ValueError:
            pass
        trace_provider.force_flush()

        reader.collect()
        metrics_data = reader.get_metrics_data()

        found_run_counter = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.workflow.run.outcomes_total":
                        found_run_counter = True
                        for data_point in metric.data.data_points:
                            if data_point.attributes.get("outcome") == "failure":
                                assert data_point.attributes.get("workflow_id") == "wf-123"
                                assert data_point.value == 1
        assert found_run_counter, "replayt.workflow.run.outcomes_total metric not found"
    finally:
        metrics.set_meter_provider(previous_meter)


def test_record_exporter_error() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(provider)

        record_exporter_error("test_error", workflow_id="wf-123", run_id="run-456")

        reader.collect()
        metrics_data = reader.get_metrics_data()

        found_error_counter = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.exporter.errors_total":
                        found_error_counter = True
                        for data_point in metric.data.data_points:
                            assert data_point.attributes.get("error_type") == "test_error"
                            assert data_point.attributes.get("workflow_id") == "wf-123"
                            assert data_point.value == 1
        assert found_error_counter, "replayt.exporter.errors_total metric not found"
    finally:
        metrics.set_meter_provider(previous_meter)


def test_duration_histogram_records_values() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(provider)

        tracer, _, trace_provider = _workflow_tracer_from_memory_exporter()
        with workflow_run_span(tracer, "wf-123", run_id="run-456"):
            pass
        trace_provider.force_flush()

        reader.collect()
        metrics_data = reader.get_metrics_data()

        found_duration_histogram = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.workflow.run.duration_ms":
                        found_duration_histogram = True
                        for data_point in metric.data.data_points:
                            assert data_point.attributes.get("workflow_id") == "wf-123"
                            assert data_point.count > 0
        assert found_duration_histogram, "replayt.workflow.run.duration_ms metric not found"
    finally:
        metrics.set_meter_provider(previous_meter)


def test_generate_run_summary_basic() -> None:
    tracer, _exporter, _provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-summary", run_id="run-summary") as span:
        summary = generate_run_summary(
            span=span,
            workflow_id="wf-summary",
            run_id="run-summary",
            outcome="success",
            high_level_steps=["init", "process", "finalize"],
        )

    assert summary.workflow_id == "wf-summary"
    assert summary.run_id == "run-summary"
    assert summary.outcome == "success"
    assert summary.high_level_steps == ["init", "process", "finalize"]
    assert summary.duration_ms >= 0
    assert summary.error_message is None
    datetime.fromisoformat(summary.start_time)
    datetime.fromisoformat(summary.end_time)


def test_generate_run_summary_with_error() -> None:
    tracer, _exporter, _provider = _workflow_tracer_from_memory_exporter()
    long_error = "e" * 150
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
    assert len(summary.error_message) == 103
    assert summary.error_message.endswith("...")


def test_run_summary_dataclass_to_dict() -> None:
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
    assert "password" not in str(summary_dict)
