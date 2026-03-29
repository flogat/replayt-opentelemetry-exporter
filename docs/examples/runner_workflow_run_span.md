# Runner.run inside `workflow_run_span`

This page shows a minimal **replayt** **`Runner`** path with **`MockLLMClient`**, wrapped by this package’s **`workflow_run_span`**, using only replayt symbols from its public **`__all__`** and an in-memory **EventStore**-shaped object (no `replayt.persistence` imports). For **`Runner`** constructor details across matrix pins, see [docs/reference-documentation/replayt-latest.md](../reference-documentation/replayt-latest.md) and [docs/reference-documentation/replayt-0.4.0.md](../reference-documentation/replayt-0.4.0.md).

## Run boundary (PUBLIC_API_SPEC §2.2.1)

Put **`workflow_run_span`** around the **single** **`Runner.run(...)`** call (and the usual **`RunResult`** → **`RunFailed`** mapping) so one logical run maps to one root span and one outcome series. Define the **`Workflow`**, attach steps, build the store, and install OpenTelemetry providers **before** the context. Call **`Runner.close`** in the same span after **`run`** returns when that teardown belongs to the same logical run.

## Example (in-memory OpenTelemetry)

After `pip install -e ".[dev]"` from the repository root, you can paste and run the script below. It mirrors PUBLIC_API_SPEC §3.3 with **in-memory** span export and metric reading instead of OTLP.

```python
from typing import Any
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from replayt import MockLLMClient, RunContext, RunFailed, Runner, Workflow
from replayt_opentelemetry_exporter import (
    get_workflow_tracer,
    install_meter_provider,
    install_tracer_provider,
    workflow_run_span,
)


class MemoryEventStore:
    """Minimal EventStore shape; same idea as contract tests (no private replayt imports)."""

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


def main() -> None:
    span_exporter = InMemorySpanExporter()
    metric_reader = InMemoryMetricReader()

    install_tracer_provider(span_exporters=[span_exporter])
    install_meter_provider(metric_readers=[metric_reader])

    wf = Workflow("runner-otel-demo")

    @wf.step("only")
    def only_step(_ctx: RunContext) -> None:
        return None

    wf.set_initial("only")
    store = MemoryEventStore()
    mock = MockLLMClient()
    run_id = f"demo-{uuid4().hex[:12]}"
    tracer = get_workflow_tracer()

    runner = Runner(wf, store, llm_client=mock)
    with workflow_run_span(tracer, wf.name, run_id=run_id):
        try:
            result = runner.run(run_id=run_id)
            if result.status != "completed":
                raise RunFailed(result.error or "run failed")
        finally:
            runner.close()

    trace.get_tracer_provider().force_flush()
    finished = span_exporter.get_finished_spans()
    assert finished
    assert finished[-1].attributes.get("replayt.workflow.outcome") == "success"


if __name__ == "__main__":
    main()
```

CI and contributors can also rely on **`tests/test_tracing.py`** — **`test_runner_run_contract_success_path_records_adapter_success`** — which calls **`Runner.run`** inside **`workflow_run_span`** and documents [TESTING_SPEC.md](../TESTING_SPEC.md) §4.2 and PUBLIC_API_SPEC §3.4 in its docstring.

## Production shape

Swap **`install_*`** + in-memory fakes for OTLP exporters (PUBLIC_API_SPEC §3.3) and a real **`llm_client`**. Keep **`workflow_run_span`** tight around **`Runner.run`** (and outcome handling) per §2.2.1.
