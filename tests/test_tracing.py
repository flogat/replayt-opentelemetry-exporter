from __future__ import annotations

import inspect
from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import StatusCode, Tracer
from replayt import (
    ContextSchemaError,
    MockLLMClient,
    RunContext,
    RunFailed,
    Runner,
    Workflow,
    run_with_mock,
)

import replayt_opentelemetry_exporter
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
    record_run_outcome,
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


def _events_named(span, name: str) -> list:
    return [e for e in span.events if e.name == name]


class _MemoryEventStore:
    """In-process store matching replayt's EventStore protocol (no replayt.persistence imports)."""

    def __init__(self) -> None:
        self._by_run: dict[str, list[dict[str, Any]]] = {}
        self._seq: dict[str, int] = {}

    def append_event(
        self, run_id: str, *, ts: str, typ: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        seq = self._seq.get(run_id, 0) + 1
        self._seq[run_id] = seq
        event: dict[str, Any] = {
            "ts": ts,
            "run_id": run_id,
            "seq": seq,
            "type": typ,
            "payload": payload,
        }
        self._by_run.setdefault(run_id, []).append(event)
        return event

    def append(self, run_id: str, event: dict[str, Any]) -> None:
        self._by_run.setdefault(run_id, []).append(event)

    def load_events(self, run_id: str) -> list[dict[str, Any]]:
        return list(self._by_run.get(run_id, []))

    def list_run_ids(self) -> list[str]:
        return sorted(self._by_run.keys())

    def delete_run(self, run_id: str) -> int:
        removed = len(self._by_run.get(run_id, []))
        self._by_run.pop(run_id, None)
        self._seq.pop(run_id, None)
        return removed


def _workflow_run_then_raise_if_failed(
    wf: Workflow, store: _MemoryEventStore, mock: MockLLMClient, *, run_id: str
) -> None:
    """Re-raise a failed RunResult as RunFailed (typical integrator pattern for tracing)."""
    res = run_with_mock(wf, store, mock, run_id=run_id)
    if res.status != "completed":
        raise RunFailed(res.error or "run failed")


def test_runner_run_contract_success_path_records_adapter_success() -> None:
    """TESTING_SPEC §4.2; PUBLIC_API_SPEC §3.4: Runner.run success path inside workflow_run_span."""
    wf = Workflow("otel-runner-contract-success")

    @wf.step("only")
    def only_step(_ctx: RunContext) -> None:
        return None

    wf.set_initial("only")
    store = _MemoryEventStore()
    mock = MockLLMClient()
    run_id = f"runner-contract-ok-{uuid4().hex[:12]}"
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    runner = Runner(wf, store, llm_client=mock)
    with workflow_run_span(tracer, wf.name, run_id=run_id):
        try:
            res = runner.run(run_id=run_id)
            if res.status != "completed":
                raise RunFailed(res.error or "run failed")
        finally:
            runner.close()
    provider.force_flush()
    span = exporter.get_finished_spans()[0]
    assert span.attributes.get("replayt.workflow.outcome") == "success"
    assert (
        _events_named(span, "replayt.workflow.run.completed")[0].attributes.get(
            "replayt.workflow.outcome"
        )
        == "success"
    )


def test_run_with_mock_contract_success_path_records_adapter_success() -> None:
    """TESTING_SPEC 4.2: run_with_mock success path inside workflow_run_span."""
    wf = Workflow("otel-contract-success")

    @wf.step("only")
    def only_step(_ctx: RunContext) -> None:
        return None

    wf.set_initial("only")
    store = _MemoryEventStore()
    mock = MockLLMClient()
    run_id = f"contract-ok-{uuid4().hex[:12]}"
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, wf.name, run_id=run_id):
        run_with_mock(wf, store, mock, run_id=run_id)
    provider.force_flush()
    span = exporter.get_finished_spans()[0]
    assert span.attributes.get("replayt.workflow.outcome") == "success"
    assert (
        _events_named(span, "replayt.workflow.run.completed")[0].attributes.get(
            "replayt.workflow.outcome"
        )
        == "success"
    )


def test_run_with_mock_contract_failed_run_surfaces_as_runtime_when_re_raises_run_failed() -> None:
    """TESTING_SPEC 4.2: RunFailed after failed mock run gets failure.category runtime."""
    wf = Workflow("otel-contract-fail")

    @wf.step("only")
    def only_step(_ctx: RunContext) -> None:
        raise ValueError("intentional step failure")

    wf.set_initial("only")
    store = _MemoryEventStore()
    mock = MockLLMClient()
    run_id = f"contract-fail-{uuid4().hex[:12]}"
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with pytest.raises(RunFailed):
        with workflow_run_span(tracer, wf.name, run_id=run_id):
            _workflow_run_then_raise_if_failed(wf, store, mock, run_id=run_id)
    provider.force_flush()
    span = exporter.get_finished_spans()[0]
    assert span.attributes.get("replayt.workflow.outcome") == "failure"
    assert span.attributes.get("replayt.workflow.failure.category") == "runtime"
    assert span.attributes.get("replayt.workflow.error.type") == "RunFailed"


def test_workflow_run_span_lifecycle_events_and_attributes_success() -> None:
    """PUBLIC_API_SPEC §6 — started + completed events and success completion attributes."""
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(tracer, "wf-123", run_id="run-456"):
        pass
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    started = _events_named(span, "replayt.workflow.run.started")
    completed = _events_named(span, "replayt.workflow.run.completed")
    assert len(started) == 1
    assert started[0].attributes == {} or started[0].attributes is None
    assert len(completed) == 1
    assert completed[0].attributes.get("replayt.workflow.outcome") == "success"
    assert span.attributes.get("replayt.workflow.outcome") == "success"
    assert "replayt.workflow.error.type" not in span.attributes
    assert "replayt.workflow.failure.category" not in span.attributes


def test_workflow_run_span_lifecycle_events_and_attributes_failure() -> None:
    """PUBLIC_API_SPEC §6 — failure path completion event mirrors span completion attributes."""
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with pytest.raises(ValueError, match="boom"):
        with workflow_run_span(tracer, "wf-123", run_id="run-456"):
            raise ValueError("boom")
    provider.force_flush()
    span = exporter.get_finished_spans()[0]
    assert _events_named(span, "replayt.workflow.run.started")
    completed = _events_named(span, "replayt.workflow.run.completed")
    assert len(completed) == 1
    attrs = completed[0].attributes
    assert attrs.get("replayt.workflow.outcome") == "failure"
    assert attrs.get("replayt.workflow.error.type") == "ValueError"
    assert attrs.get("replayt.workflow.failure.category") == "validation"
    assert span.attributes.get("replayt.workflow.outcome") == "failure"
    assert span.attributes.get("replayt.workflow.error.type") == "ValueError"
    assert span.attributes.get("replayt.workflow.failure.category") == "validation"


@pytest.mark.parametrize(
    ("exc_factory", "expected_category"),
    [
        (lambda: TimeoutError(), "timeout"),
        (lambda: ConnectionError(), "external_dependency"),
        (lambda: RunFailed(), "runtime"),
        (lambda: ContextSchemaError("step", []), "validation"),
        (lambda: KeyError("missing"), "unknown"),
    ],
)
def test_workflow_run_span_failure_category_mapping(exc_factory, expected_category: str) -> None:
    """PUBLIC_API_SPEC §6.4 — documented exception to failure.category mapping."""
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    exc = exc_factory()
    with pytest.raises(type(exc)):
        with workflow_run_span(tracer, "wf-cat"):
            raise exc
    provider.force_flush()
    span = exporter.get_finished_spans()[0]
    assert span.attributes.get("replayt.workflow.failure.category") == expected_category
    assert (
        _events_named(span, "replayt.workflow.run.completed")[0].attributes.get(
            "replayt.workflow.failure.category"
        )
        == expected_category
    )


def test_package_all_exports_match_public_api_spec_section3() -> None:
    """Lock top-level exports to docs/PUBLIC_API_SPEC.md §3."""
    expected = frozenset(
        {
            "__version__",
            "build_resource",
            "build_tracer_provider",
            "build_meter_provider",
            "install_tracer_provider",
            "install_meter_provider",
            "get_workflow_tracer",
            "workflow_run_span",
            "RunSummary",
            "generate_run_summary",
            "record_run_outcome",
            "record_exporter_error",
        }
    )
    assert frozenset(replayt_opentelemetry_exporter.__all__) == expected


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
    assert spans[0].attributes["replayt.workflow.outcome"] == "success"
    assert spans[0].status.status_code == StatusCode.OK


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
    assert spans[0].end_time is not None


def test_workflow_run_span_error_status_description_omits_message_body() -> None:
    """Span status description must stay type-only so long or sensitive str(exc) is not exported."""
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    sensitive = "Bearer deadbeef" * 20
    with pytest.raises(RuntimeError):
        with workflow_run_span(tracer, "wf-123"):
            raise RuntimeError(sensitive)
    provider.force_flush()
    spans = exporter.get_finished_spans()
    assert spans[0].status.description == "RuntimeError"
    assert sensitive not in (spans[0].status.description or "")


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


# SECURITY_REDACTION.md + PUBLIC_API_SPEC §6 — optional span attributes; redaction matrices below.


@pytest.mark.parametrize(
    "blocked_key",
    sorted(tracing_mod._EXACT_BLOCKED_ATTRIBUTE_KEYS),
)
def test_workflow_run_span_omits_exact_blocked_attribute_keys(blocked_key: str) -> None:
    """SECURITY_REDACTION.md; PUBLIC_API_SPEC §6 — optional span attrs, exact blocked-key matrix."""
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(
        tracer,
        "wf-123",
        attributes={blocked_key: "credential-like-value", "region": "eu"},
    ):
        pass
    provider.force_flush()
    attrs = exporter.get_finished_spans()[0].attributes
    assert blocked_key not in attrs
    assert attrs["region"] == "eu"


@pytest.mark.parametrize(
    "blocked_key",
    [
        "my_password_hint",
        "legacy_passwd_field",
        "integration_api_key_name",
        "vendorapikeyfield",
        "oauth_access_token",
        "signing_secret",
        "BeArEr",
    ],
)
def test_workflow_run_span_omits_blocked_keys_substring_suffix_and_case(
    blocked_key: str,
) -> None:
    """SECURITY_REDACTION.md; PUBLIC_API_SPEC §6 — substring, _token/_secret suffix, lowercasing."""
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(
        tracer,
        "wf-123",
        attributes={blocked_key: "should-not-export", "allowed.safe": "kept"},
    ):
        pass
    provider.force_flush()
    attrs = exporter.get_finished_spans()[0].attributes
    assert blocked_key not in attrs
    assert attrs["allowed.safe"] == "kept"


@pytest.mark.parametrize(
    ("raw_len", "expected_len"),
    [
        (99, 99),
        (100, 100),
        (101, 100),
        (150, 100),
    ],
)
def test_workflow_run_span_truncates_optional_attributes_at_100_codepoints(
    raw_len: int, expected_len: int
) -> None:
    """SECURITY_REDACTION.md; PUBLIC_API_SPEC §6 — 100 code-point cap, no ellipsis on attrs."""
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    payload = "x" * raw_len
    with workflow_run_span(tracer, "wf-123", attributes={"note": payload}):
        pass
    provider.force_flush()
    got = exporter.get_finished_spans()[0].attributes["note"]
    assert len(got) == expected_len
    assert got == payload[:100]


@pytest.mark.parametrize(
    ("workflow_id", "run_id", "extra_attrs"),
    [
        (
            "wf-canonical",
            "run-canonical",
            {
                "replayt.workflow.id": "wf-evil",
                "replayt.run.id": "run-evil",
                "custom.dim": "ok",
            },
        ),
        (
            "wf-only",
            None,
            {"replayt.run.id": "run-evil", "custom.dim": "ok"},
        ),
        (
            "wf-only",
            "run-ok",
            {"replayt.workflow.id": "wf-evil", "custom.dim": "ok"},
        ),
        (
            "wf-only",
            None,
            {"replayt.workflow.id": "wf-evil", "custom.dim": "ok"},
        ),
    ],
)
def test_workflow_run_span_reserved_keys_in_attributes_do_not_override(
    workflow_id: str,
    run_id: str | None,
    extra_attrs: dict[str, str],
) -> None:
    """SECURITY_REDACTION.md; PUBLIC_API_SPEC §6 — reserved workflow/run id keys not overridden."""
    tracer, exporter, provider = _workflow_tracer_from_memory_exporter()
    with workflow_run_span(
        tracer,
        workflow_id,
        run_id=run_id,
        attributes=extra_attrs,
    ):
        pass
    provider.force_flush()
    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["replayt.workflow.id"] == workflow_id
    if run_id is not None:
        assert attrs["replayt.run.id"] == run_id
    else:
        assert "replayt.run.id" not in attrs
    assert attrs["custom.dim"] == "ok"


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


def test_public_api_spec_semantic_inventory_matches_tracing() -> None:
    """TESTING_SPEC §5 item 5; PUBLIC_API_SPEC §5.7, §6.8 — canonical names match shipped code.

    Renames MUST update this test, docs/PUBLIC_API_SPEC.md §5–§6 / §5.7 / §6.8, and CHANGELOG
    per §8 item 15. Optional integrator-only event ``replayt.workflow.milestone`` (§6.2) is not
    emitted by this package and has no module constant.
    """
    sig = inspect.signature(workflow_run_span)
    assert sig.parameters["span_name"].default == "replayt.workflow.run"

    assert tracing_mod._EVENT_WORKFLOW_RUN_STARTED == "replayt.workflow.run.started"
    assert tracing_mod._EVENT_WORKFLOW_RUN_COMPLETED == "replayt.workflow.run.completed"
    assert tracing_mod._ATTR_WORKFLOW_OUTCOME == "replayt.workflow.outcome"
    assert tracing_mod._ATTR_ERROR_TYPE == "replayt.workflow.error.type"
    assert tracing_mod._ATTR_FAILURE_CATEGORY == "replayt.workflow.failure.category"

    resource = build_resource(service_name="contract-svc")
    assert resource.attributes.get("service.name") == "contract-svc"
    assert "service.version" in resource.attributes

    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(provider)
        record_run_outcome(True, "wf-inv", duration_ms=1.0)
        record_exporter_error("timeout")
        reader.collect()
        data = reader.get_metrics_data()
        scope_names: set[str] = set()
        instrument_names: set[str] = set()
        for rm in data.resource_metrics:
            for sm in rm.scope_metrics:
                scope_names.add(sm.scope.name)
                for metric in sm.metrics:
                    instrument_names.add(metric.name)
        assert scope_names == {"replayt.workflow"}
        assert instrument_names == {
            "replayt.workflow.run.outcomes_total",
            "replayt.workflow.run.duration_ms",
            "replayt.exporter.errors_total",
        }
    finally:
        metrics.set_meter_provider(previous_meter)


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
                            assert data_point.attributes.get("run_id") == "run-456"
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
                                assert data_point.attributes.get("run_id") == "run-456"
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

        record_exporter_error("export_failed", workflow_id="wf-123", run_id="run-456")

        reader.collect()
        metrics_data = reader.get_metrics_data()

        found_error_counter = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.exporter.errors_total":
                        found_error_counter = True
                        for data_point in metric.data.data_points:
                            assert data_point.attributes.get("error_type") == "export_failed"
                            assert data_point.attributes.get("workflow_id") == "wf-123"
                            assert data_point.attributes.get("run_id") == "run-456"
                            assert data_point.value == 1
        assert found_error_counter, "replayt.exporter.errors_total metric not found"
    finally:
        metrics.set_meter_provider(previous_meter)


@pytest.mark.parametrize(
    "error_type",
    ("export_failed", "serialization_error", "timeout", "unknown"),
)
def test_record_exporter_error_recommended_types_passthrough(error_type: str) -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(provider)
        record_exporter_error(error_type)
        reader.collect()
        metrics_data = reader.get_metrics_data()
        found = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.exporter.errors_total":
                        for dp in metric.data.data_points:
                            if dp.attributes.get("error_type") == error_type:
                                found = True
                                assert dp.value == 1
        assert found, f"expected error_type={error_type!r} data point"
    finally:
        metrics.set_meter_provider(previous_meter)


def test_record_exporter_error_coerces_non_recommended_to_unknown() -> None:
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(provider)
        record_exporter_error("custom_vendor_code_500")
        reader.collect()
        metrics_data = reader.get_metrics_data()
        found = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.exporter.errors_total":
                        for dp in metric.data.data_points:
                            assert dp.attributes.get("error_type") == "unknown"
                            assert dp.value == 1
                            found = True
        assert found
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
                            assert data_point.attributes.get("outcome") == "success"
                            assert data_point.attributes.get("run_id") == "run-456"
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


@pytest.mark.parametrize(
    ("success", "expected_outcome"),
    [(True, "success"), (False, "failure")],
)
def test_record_run_outcome_metrics_without_workflow_run_span(
    success: bool,
    expected_outcome: str,
) -> None:
    """TESTING_SPEC §4.7; PUBLIC_API_SPEC §3.5, §5.5.3 — §5 labels without workflow_run_span."""
    reader = InMemoryMetricReader()
    provider = build_meter_provider(metric_readers=[reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(provider)
        workflow_id = "wf-advanced-metrics"
        run_id = "run-adv-1"
        duration_ms = 10.0
        record_run_outcome(
            success,
            workflow_id,
            run_id=run_id,
            duration_ms=duration_ms,
        )
        reader.collect()
        metrics_data = reader.get_metrics_data()

        found_counter = False
        found_hist = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.workflow.run.outcomes_total":
                        for dp in metric.data.data_points:
                            if dp.attributes.get("outcome") == expected_outcome:
                                assert dp.attributes.get("workflow_id") == workflow_id
                                assert dp.attributes.get("run_id") == run_id
                                assert dp.value == 1
                                found_counter = True
                    if metric.name == "replayt.workflow.run.duration_ms":
                        for dp in metric.data.data_points:
                            if dp.attributes.get("outcome") == expected_outcome:
                                assert dp.attributes.get("workflow_id") == workflow_id
                                assert dp.attributes.get("run_id") == run_id
                                assert dp.count > 0
                                found_hist = True
        assert found_counter
        assert found_hist
    finally:
        metrics.set_meter_provider(previous_meter)


def test_record_run_outcome_paired_with_generate_run_summary_integrator_span() -> None:
    """TESTING_SPEC §4.7; PUBLIC_API_SPEC §3.5, §5.5.2 — pairing on an integrator-owned span."""
    tracer, span_exporter, trace_provider = _workflow_tracer_from_memory_exporter()
    metric_reader = InMemoryMetricReader()
    meter_provider = build_meter_provider(metric_readers=[metric_reader])
    previous_meter = metrics.get_meter_provider()
    try:
        metrics.set_meter_provider(meter_provider)
        workflow_id = "wf-pair-summary"
        run_id = "run-pair-summary"
        with tracer.start_as_current_span("integrator.owned.run") as span:
            span.set_attribute("replayt.workflow.id", workflow_id)
            span.set_attribute("replayt.run.id", run_id)

        assert span.end_time is not None
        elapsed_ns = span.end_time - span.start_time
        duration_ms = elapsed_ns / 1e6

        record_run_outcome(
            success=True,
            workflow_id=workflow_id,
            run_id=run_id,
            duration_ms=duration_ms,
        )

        summary = generate_run_summary(
            span=span,
            workflow_id=workflow_id,
            run_id=run_id,
            outcome="success",
            high_level_steps=["dispatch", "finish"],
        )

        assert summary.workflow_id == workflow_id
        assert summary.run_id == run_id
        assert summary.outcome == "success"
        assert summary.high_level_steps == ["dispatch", "finish"]
        assert summary.duration_ms == int(elapsed_ns / 1e6)
        datetime.fromisoformat(summary.start_time)
        datetime.fromisoformat(summary.end_time)

        metric_reader.collect()
        metrics_data = metric_reader.get_metrics_data()
        found_counter = False
        for rm in metrics_data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    if metric.name == "replayt.workflow.run.outcomes_total":
                        for dp in metric.data.data_points:
                            if dp.attributes.get("outcome") == "success":
                                assert dp.attributes.get("workflow_id") == workflow_id
                                assert dp.attributes.get("run_id") == run_id
                                assert dp.value == 1
                                found_counter = True
        assert found_counter

        trace_provider.force_flush()
        finished = span_exporter.get_finished_spans()
        assert len(finished) == 1
        event_names = [e.name for e in finished[0].events]
        assert "replayt.workflow.run.started" not in event_names
        assert "replayt.workflow.run.completed" not in event_names
    finally:
        metrics.set_meter_provider(previous_meter)


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
