from unittest.mock import patch
from datetime import datetime

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Tracer

from replayt_opentelemetry_exporter import (
    build_resource,
    build_tracer_provider,
    get_workflow_tracer,
    install_tracer_provider,
    workflow_run_span,
    generate_run_summary,
    RunSummary,
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
