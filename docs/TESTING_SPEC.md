# Automated testing: replayt boundary and exporter behavior

This document is the **specification** for backlog item *Implement automated tests for replayt boundary and exporter behavior*. It turns the backlog acceptance criteria into **testable obligations** for maintainers and for the **Builder** phase that adds or extends `tests/` and CI.

It aligns with **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** (**Explicit contracts**, **Observable automation**): behavior we claim in **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)** and **[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md)** stays covered by pytest, with deterministic fakes where possible.

## 1. Purpose

- **Contributors** run one documented command locally and get **standard process exit codes** (pytest: `0` = all passed, non-zero = failures/errors).
- **CI** runs the same checks as documented for humans (see **§3**), so regressions on the replayt integration seam and exporter-side signals are caught before merge.
- **Reviewers** can point to this spec when asking whether a change needs a new assertion or scenario.

## 2. Backlog acceptance mapping

The backlog item *Implement automated tests for replayt boundary and exporter behavior* is satisfied when:

| Backlog acceptance criterion | Normative requirement in this spec |
| ---------------------------- | ----------------------------------- |
| Tests run via documented command (e.g. pytest) | **§3.1** — primary command is `pytest` from the repository root after `pip install -e ".[dev]"`. |
| At least one test exercises **success** and one exercises **failure** or **export error** path | **§4.3** — success path for run lifecycle; **§4.4** — failure path inside `workflow_run_span`; **§4.5** — exporter / export-health path via `replayt.exporter.errors_total` (or equivalent span/export failure signal once implemented). |
| CI or local script documents how to run the suite with clear exit codes | **§3.2** — README and **[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) §4** reference `.github/workflows/ci.yml`; pytest exit codes are standard (no custom wrapper required unless the project adds one later). |

## 3. How to run tests (normative)

### 3.1 Local default

From the **repository root** after a dev install:

```bash
pip install -e ".[dev]"
pytest
```

Match maintainer expectations with **`python -m ruff check src tests`** and **`python -m ruff format --check src tests`** (same as README **Running tests and lint locally** and [CI_SPEC.md](CI_SPEC.md) **§3.1**).

### 3.2 CI parity

The canonical automation is **[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)** job **`test`**: each matrix cell runs Ruff then **the same `pytest` invocation** contributors use (no alternate test runner unless documented in this spec and README). **Step naming, exit-code propagation, and safe CI logs** for that job are normative in **[CI_SPEC.md](CI_SPEC.md)**.

### 3.3 Exit codes

- **pytest:** Process exit code **`0`** when all tests pass; **non-zero** on failures, errors, or interrupted runs. Custom scripts MUST NOT remap pytest’s exit codes unless README and this section are updated together.

## 4. Test strategy

### 4.1 Determinism and fakes

- **Prefer in-process, deterministic doubles:** `InMemorySpanExporter`, `InMemoryMetricReader`, and providers built via **`build_tracer_provider` / `build_meter_provider`** (see [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §3) rather than real OTLP endpoints or network exporters, unless a test is explicitly scoped to optional OTLP extras.
- **Avoid flakiness:** Do not assert on wall-clock timing bands narrower than what the CI environment can satisfy; histogram tests SHOULD assert presence of recorded values and labels, not exact latency ms, unless using controlled clocks/fakes.

### 4.2 Layers (what “unit” vs “contract” means here)

| Layer | Intent | Replayt usage |
| ----- | ------ | --------------- |
| **Unit (package-local)** | Provider wiring, metric names, span lifecycle, redaction of attributes, `record_exporter_error` normalization | MAY use replayt **only** for exception types that are part of the public API (e.g. `RunFailed`, `ContextSchemaError`) when testing [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§6.4** mapping—**no** private replayt imports. |
| **Contract-style (integration seam)** | Prove the adapter behaves correctly when replayt-shaped failures (and, where practical, a **minimal** successful replayt run) occur **inside** `workflow_run_span` | SHOULD include at least one scenario that exercises **replayt’s public** workflow/run path **or** documented helpers (e.g. `run_with_mock`, `Runner` / `Workflow`) **without** importing replayt internals; if a full run is impractical in CI, the **minimum** contract bar remains: public replayt **exception types** raised inside the wrapped block are classified per §6.4 (see existing parametrized mapping tests as the pattern). |

### 4.3 Success path (minimum)

Automated tests MUST assert that a **successful** completion of `workflow_run_span` (or documented equivalent) produces at least:

- Span status OK and [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§6** lifecycle signals (e.g. `replayt.workflow.run.started`, `replayt.workflow.run.completed` with `replayt.workflow.outcome` = `success` on the event and span where applicable).
- Outcome metrics per **§5** (e.g. `replayt.workflow.run.outcomes_total` with `outcome` = `success`) when the global meter provider is configured per spec.

### 4.4 Failure path (minimum)

Automated tests MUST assert that when the wrapped block **raises**, the adapter:

- Ends the span, sets ERROR status with **safe** description (exception **type name** only), sets **§6** failure completion attributes/events, records **failure** outcome metrics, and **re-raises** the same exception ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§4**).

### 4.5 Export / exporter error path (minimum)

Automated tests MUST include at least one scenario for **export health** independent of a successful workflow run:

- **`record_exporter_error`** (or the implementation’s equivalent) records **`replayt.exporter.errors_total`** with a normalized `error_type` per [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5.3**, including a case where a non-recommended string is coerced to `unknown`.

If the project later adds automatic export-failure handling inside span processors, extend tests to assert the same metric or documented span signal—update this section in the same change.

### 4.6 Dependency and matrix hygiene

- **`tests/test_pyproject_dependencies.py`** (or successor) SHOULD remain the place for **declared** `pyproject.toml` bound checks unless CONTRIBUTING says otherwise.
- Matrix cells in CI MUST continue to run the **full** pytest suite unless a documented subset is approved in this spec and README (default: **full suite**).

## 5. Builder acceptance checklist

The **implementation** backlog for this item is complete when all of the following hold:

1. **§2** acceptance mapping is satisfied by the test tree and CI.
2. **§4.3–§4.5** minimum scenarios exist and are named or documented in test docstrings referencing the spec sections they lock.
3. **No replayt private API** imports in `tests/` (only public `replayt` symbols and this package’s API).
4. **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §8** item **6** remains true: tests cover span lifecycle, §6 attributes/events, success/failure metrics, provider installation, and `__all__` parity as specified there; gaps are tracked under **Unreleased** in [CHANGELOG.md](../CHANGELOG.md) if intentionally deferred.

## 6. Related documents

- [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) — run boundary, metrics, lifecycle, §8 Builder checklist.
- [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) — CI matrix and local reproduction.
- [CI_SPEC.md](CI_SPEC.md) — Ruff + pytest workflow steps, failure surfacing, CI log hygiene.
- [README.md](../README.md) — contributor commands.
- [CHANGELOG.md](../CHANGELOG.md) — release-facing notes when test obligations change.
