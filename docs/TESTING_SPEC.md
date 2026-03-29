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

The canonical automation is **[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)** job **`test`**: each matrix cell runs Ruff then **the same `pytest` invocation** contributors use (no alternate test runner unless documented in this spec and README). **Step naming, exit-code propagation, and safe CI logs** for that job are normative in **[CI_SPEC.md](CI_SPEC.md)**. Merge gate cells include **Python 3.11** and **3.12** for the **full** replayt×OpenTelemetry matrix ([COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1**, [CI_SPEC.md](CI_SPEC.md) **§3.6**).

### 3.3 Exit codes

- **pytest:** Process exit code **`0`** when all tests pass; **non-zero** on failures, errors, or interrupted runs. Custom scripts MUST NOT remap pytest’s exit codes unless README and this section are updated together.

### 3.4 Optional PyPI index check (maintainers)

**[`tests/test_pypi_index.py`](../tests/test_pypi_index.py)** is **skipped** unless the environment sets **`VERIFY_PYPI_INDEX=1`** (or **`true`** / **`yes`**). It requests the PyPI JSON API for **`replayt-opentelemetry-exporter`** and asserts the published **`info.version`** matches **`[project].version`** in **`pyproject.toml`**, with **`info.name`** normalized to the canonical distribution name ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§8** item **17**). Default **`pytest`** and CI omit this variable so the merge gate stays offline-safe. README **Releases and PyPI** documents the exact command.

## 4. Test strategy

### 4.1 Determinism and fakes

- **Prefer in-process, deterministic doubles:** `InMemorySpanExporter`, `InMemoryMetricReader`, and providers built via **`build_tracer_provider` / `build_meter_provider`** (see [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §3) rather than real OTLP endpoints or network exporters, unless a test is explicitly scoped to optional OTLP extras.
- **Avoid flakiness:** Do not assert on wall-clock timing bands narrower than what the CI environment can satisfy; histogram tests SHOULD assert presence of recorded values and labels, not exact latency ms, unless using controlled clocks/fakes.

### 4.2 Layers (what “unit” vs “contract” means here)

| Layer | Intent | Replayt usage |
| ----- | ------ | --------------- |
| **Unit (package-local)** | Provider wiring, metric names, span lifecycle, redaction of attributes, `record_exporter_error` normalization | MAY use replayt **only** for exception types that are part of the public API (e.g. `RunFailed`, `ContextSchemaError`) when testing [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§6.4** mapping—**no** private replayt imports. |
| **Contract-style (integration seam)** | Prove the adapter behaves correctly when replayt-shaped failures (and, where practical, a **minimal** successful replayt run) occur **inside** `workflow_run_span` | MUST include at least one scenario using **`run_with_mock`** (existing pattern) **and** MUST satisfy [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§3.4** runnability: either **(i)** a pytest contract that invokes **`Runner.run`** inside **`workflow_run_span`** on a **success** path (and, where practical, documents alignment with failure handling), **or** **(ii)** a standalone runnable script documented in **§3.4** so CI is not the only proof. **Only** replayt **`__all__`** symbols and **EventStore**-compatible in-memory stores (no private replayt imports). Any **`Runner.run`** pytest **MUST** mention **`TESTING_SPEC §4.2`** and **PUBLIC_API_SPEC §3.4** in its docstring. If a full **`Runner`** failure-path contract is impractical, the **minimum** bar remains public replayt **exception types** raised inside the wrapped block classified per §6.4 (see parametrized mapping tests)—**without** dropping the **`Runner.run`** success-path obligation when **§3.4** chooses the pytest option. |

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

When [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5.5.1** automatic export-failure recording is implemented, tests MUST additionally prove the hook **without a real remote collector**:

| Obligation | Detail |
| ---------- | ------ |
| **Fake failure** | Use an in-process **`SpanExporter`** (and, if **§5.5.1** covers metrics, a **`MetricExporter`** or reader setup) that **fails** `export` deterministically, wired through the same **`build_tracer_provider` / `install_tracer_provider`** (and meter equivalents) path integrators use with the opt-in flag **on**. |
| **Success control** | With the same wiring except the exporter succeeds (or opt-in **off**), assert **`replayt.exporter.errors_total`** does **not** increase for that scenario—so the hook is not firing on every batch or healthy export. |
| **Normalized label** | On failure, assert exactly one increment (per logical failure the hook owns) with **`error_type`** in the **§5.3** set (matching the implementation’s mapping from the injected failure). |
| **Default off** | Assert that **default** provider installation (opt-in **off**) does **not** register automatic hooks that change **`errors_total`** compared to pre-**§5.5.1** behavior for the same fake exporter failure **unless** the integrator already called `record_exporter_error` in test setup—i.e. automatic recording is truly opt-in. |

Maintainers MAY satisfy the **`record_exporter_error`** bullet and the **§5.5.1** table in one test module or split them; docstrings MUST cite **§4.5** and, for hook tests, **PUBLIC_API_SPEC §5.5.1**.

### 4.6 Dependency and matrix hygiene

- **`tests/test_pyproject_dependencies.py`** (or successor) SHOULD remain the place for **declared** `pyproject.toml` bound checks unless CONTRIBUTING says otherwise. When maintainers widen or narrow OpenTelemetry bounds (including any future **2.x** claim), update those assertions **in the same change** as `pyproject.toml` so CI cannot drift from the spec.
- **replayt open upper (today):** While [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§3.3** allows a lower bound only, **`test_replayt_specifier_open_upper_matches_ci_latest_row`** keeps declared bounds aligned with merge-gate cells that reinstall **`replayt`** with **`latest`**: the specifier must still contain the documented floor and a high sentinel version. After a known-breaking replayt release, maintainers add the cap in **`pyproject.toml`**, replace this test with checks that the floor remains inside the specifier and a representative excluded version does not, and update README, [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§7.3**, and the workflow matrix **in the same change**.
- **OTLP gRPC extra:** When **`[otlp-grpc]`** ships ([COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§3.4.2**), the same module SHOULD assert that **`opentelemetry-exporter-otlp-proto-grpc`** specifiers **match** **`opentelemetry-exporter-otlp-proto-http`** in **`[otlp]`** (parallel to the existing **`test_pyproject_otlp_extra_aligns_with_api_sdk_otel_bounds`** test). Network export to a collector remains **out of scope** unless a future spec requires it (**§4.1** fakes-first rule).
- Matrix cells in CI MUST continue to run the **full** pytest suite unless a documented subset is approved in this spec and README (default: **full suite**).
- **OpenTelemetry 2.x:** Do not expect **2.x**-pinned matrix cells until [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7** is satisfied end-to-end (spike, **§7.3** documentation outcome, **§7.4** matrix expansion rules). When **2.x** cells exist, they MUST run the **full** suite like **1.x** cells, and **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §8** item **12** MUST be satisfied for the release.

## 5. Builder acceptance checklist

The **implementation** backlog for this item is complete when all of the following hold:

1. **§2** acceptance mapping is satisfied by the test tree and CI.
2. **§4.3–§4.5** minimum scenarios exist and are named or documented in test docstrings referencing the spec sections they lock (including **§4.5** **`record_exporter_error`** coverage and, once **§5.5.1** ships, in-process exporter failure fakes per the **§4.5** table); **§4.2** contract row is satisfied including [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§3.4** (`run_with_mock` **and** **`Runner.run`** **or** documented script per that section).
3. **No replayt private API** imports in `tests/` (only public `replayt` symbols and this package’s API).
4. **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §8** item **6** remains true: tests cover span lifecycle, §6 attributes/events, success/failure metrics, provider installation, and `__all__` parity as specified there; gaps are tracked under **Unreleased** in [CHANGELOG.md](../CHANGELOG.md) if intentionally deferred.
5. **Semantic convention identifiers:** Any test that asserts literal span names, lifecycle event names, span attribute keys, metric instrument names, or meter scope strings stays consistent with [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5–§6** and the inventory in **§5.7** / **§6.8**; renames update those tests **in the same change** as the spec, operator runbook (if PromQL or narrative references the old name), and [CHANGELOG.md](../CHANGELOG.md) per **§8** item **15**.

## 6. Related documents

- [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) — run boundary, metrics, lifecycle, semantic convention alignment (**§5.7**, **§6.8**), §8 Builder checklist.
- [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) — CI matrix and local reproduction.
- [CI_SPEC.md](CI_SPEC.md) — Ruff + pytest workflow steps, failure surfacing, CI log hygiene.
- [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) — optional **version drift** tests; placement per that document **§6.4**; optional PyPI index proof per **§3.4** here and [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§8** item **17**.
- [README.md](../README.md) — contributor commands.
- [CHANGELOG.md](../CHANGELOG.md) — release-facing notes when test obligations change.
