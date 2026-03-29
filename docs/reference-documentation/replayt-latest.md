**Source:** `replayt==0.4.25`  
**Snapshot date:** 2026-03-29

Curated notes for **PyPI latest** at the snapshot date, matching the CI matrix **latest** cell (reinstall). When you upgrade replayt locally, compare with this file and with [replayt-0.4.0.md](replayt-0.4.0.md) for drift. Full docstrings: your installed wheel or [PyPI](https://pypi.org/project/replayt/).

## `Workflow`

Same constructor shape as **0.4.0**:

```text
(name: str, *, version: str = '1', meta: dict[str, Any] | None = None, llm_defaults: dict[str, Any] | None = None) -> None
```

Finite-state workflow definition with explicit handlers and optional metadata.

## `Runner`

At **0.4.25**, **Runner** adds optional **`redact_keys`** and **`policy_hooks`** compared to **0.4.0**:

```text
(workflow: Workflow, store: EventStore, *, llm_settings: LLMSettings | None = None, log_mode: LogMode = LogMode.redacted, llm_client: OpenAICompatClient | None = None, include_tracebacks: bool = False, max_steps: int | None = None, before_step: Callable[[RunContext, str], None] | None = None, after_step: Callable[[RunContext, str, str | None], None] | None = None, redact_keys: list[str] | tuple[str, ...] | None = None, policy_hooks: dict[str, Any] | None = None) -> None
```

Otherwise same role: execute **workflow** against **store**, emit structured events, optional **before_step** / **after_step** with **RunContext**.

## `RunContext`

```text
(runner: Runner, *, llm_defaults: dict[str, Any] | None = None) -> None
```

Mutable per-run bag and LLM/tools facades (unchanged vs **0.4.0** at the type level).

## `run_with_mock`

```text
(wf: Workflow, store: EventStore, mock: MockLLMClient, *, inputs: dict[str, Any] | None = None, run_id: str | None = None, resume: bool = False, log_mode: LogMode = LogMode.redacted) -> RunResult
```

Same signature as **0.4.0**: run **wf** with **MockLLMClient** for tests or offline runs.
