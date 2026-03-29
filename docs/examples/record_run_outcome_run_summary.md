# `record_run_outcome` with `generate_run_summary` (no `workflow_run_span`)

This page is for integrators who **cannot** wrap the full run in **`workflow_run_span`** but still want **§5** outcome (and optional duration) metrics plus a **`RunSummary`** for support-style artifacts. Normative rules live in [PUBLIC_API_SPEC.md](../PUBLIC_API_SPEC.md) **§5.5** and **§3.5**; **`RunSummary`** fields are defined in [RUN_SUMMARY_SPEC.md](../RUN_SUMMARY_SPEC.md).

## Meter and tracer setup

Install a **global** meter provider with this package’s **`build_meter_provider`** / **`install_meter_provider`** **before** calling **`record_run_outcome`**. If the global provider was never wired this way, the package’s module-level instruments stay unset and **`record_run_outcome`** records nothing (no exception). **`generate_run_summary`** does not touch metrics.

Install a tracer provider the same way as in [docs/examples/runner_workflow_run_span.md](runner_workflow_run_span.md) (in-memory below, OTLP in production per **§3.3**).

## Outcome strings must match

For one logical run, **`record_run_outcome(success=...)`** and the **`outcome`** argument to **`generate_run_summary`** must agree: **`success=True`** with an outcome that means success (here **`"success"`**); **`success=False`** with a failure token such as **`"failure"`**. Metrics do not fill **`RunSummary`**; mixing booleans and strings inconsistently is an integrator bug.

## Threading and async

Global OpenTelemetry providers are process-wide. Call **`record_run_outcome`** and **`generate_run_summary`** from the completion path that owns the run (or after the awaited work finishes) so span **`end_time`** and wall-clock duration line up. This package does not add async context managers; propagate trace context per your tracer API if work crosses **`await`**.

## Example (in-memory OpenTelemetry)

After `pip install -e ".[dev]"` from the repository root, you can paste and run the script below. It opens an integrator-owned span (not **`workflow_run_span`**), ends it, then records metrics and builds a summary.

```python
from uuid import uuid4

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from replayt_opentelemetry_exporter import (
    generate_run_summary,
    get_workflow_tracer,
    install_meter_provider,
    install_tracer_provider,
    record_run_outcome,
)


def main() -> None:
    span_exporter = InMemorySpanExporter()
    metric_reader = InMemoryMetricReader()

    install_tracer_provider(span_exporters=[span_exporter])
    install_meter_provider(metric_readers=[metric_reader])

    workflow_id = "custom-scheduler-wf"
    run_id = f"run-{uuid4().hex[:12]}"
    tracer = get_workflow_tracer()

    with tracer.start_as_current_span("myapp.workflow.run") as span:
        span.set_attribute("replayt.workflow.id", workflow_id)
        span.set_attribute("replayt.run.id", run_id)

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
        high_level_steps=["dispatch", "execute", "finalize"],
    )

    trace.get_tracer_provider().force_flush()
    metrics.get_meter_provider().force_flush()

    assert summary.workflow_id == workflow_id
    assert summary.run_id == run_id
    assert summary.outcome == "success"
    assert summary.duration_ms == int(elapsed_ns / 1e6)

    metric_reader.collect()
    data = metric_reader.get_metrics_data()
    names = {
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    }
    assert "replayt.workflow.run.outcomes_total" in names
    assert "replayt.workflow.run.duration_ms" in names

    finished = span_exporter.get_finished_spans()
    assert finished
    assert finished[-1].name == "myapp.workflow.run"


if __name__ == "__main__":
    main()
```

## Runnability and tests

This snippet is executable as a script. CI and contributors can also rely on **`tests/test_tracing.py`** — **`test_record_run_outcome_metrics_without_workflow_run_span`** and **`test_record_run_outcome_paired_with_generate_run_summary_integrator_span`** — which cite [TESTING_SPEC.md](../TESTING_SPEC.md) **§4.7** and PUBLIC_API_SPEC **§3.5** / **§5.5**.

## Production shape

Swap **`install_*`** + in-memory fakes for OTLP exporters ([PUBLIC_API_SPEC.md](../PUBLIC_API_SPEC.md) **§3.3**). Keep the integrator span’s lifetime aligned with the real run; **`generate_run_summary`** reads **`start_time`** / **`end_time`** from that span only.
