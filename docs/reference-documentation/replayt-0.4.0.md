**Source:** `replayt==0.4.0`  
**Snapshot date:** 2026-03-29

Curated notes for the workflow/run backbone this adapter wraps. Full text: install `replayt==0.4.0` and use `help(replayt.Workflow)` (and siblings) or the [PyPI project page](https://pypi.org/project/replayt/0.4.0/).

## `Workflow`

Constructor:

```text
(name: str, *, version: str = '1', meta: dict[str, Any] | None = None, llm_defaults: dict[str, Any] | None = None) -> None
```

Finite-state workflow definition with explicit handlers and optional metadata. Build a graph of steps; execution is driven by **Runner**.

## `Runner`

Constructor:

```text
(workflow: Workflow, store: EventStore, *, llm_settings: LLMSettings | None = None, log_mode: LogMode = LogMode.redacted, llm_client: OpenAICompatClient | None = None, include_tracebacks: bool = False, max_steps: int | None = None, before_step: Callable[[RunContext, str], None] | None = None, after_step: Callable[[RunContext, str, str | None], None] | None = None) -> None
```

Runs **workflow** against **store**, emitting structured events. Hooks **before_step** / **after_step** receive **RunContext** and step identifiers—useful when correlating OTel spans with step boundaries in your own code (this repo still treats one **workflow run** as the primary span boundary per [PUBLIC_API_SPEC.md](../PUBLIC_API_SPEC.md) **§2**).

## `RunContext`

Constructor:

```text
(runner: Runner, *, llm_defaults: dict[str, Any] | None = None) -> None
```

Mutable per-run state and facades for LLM/tools during a run.

## `run_with_mock`

```text
(wf: Workflow, store: EventStore, mock: MockLLMClient, *, inputs: dict[str, Any] | None = None, run_id: str | None = None, resume: bool = False, log_mode: LogMode = LogMode.redacted) -> RunResult
```

Runs **wf** with a **MockLLMClient** instead of a live provider—typical for tests and for integrators who want a single call path to wrap with `workflow_run_span` (see this package’s tests).
