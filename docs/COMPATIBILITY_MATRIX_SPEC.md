# Compatibility matrix and dependency pins

This document is the **specification** for backlog item *Add compatibility matrix and dependency pins for replayt and OpenTelemetry*. It turns the backlog acceptance criteria into **testable obligations** for maintainers and for the **Builder** phase that edits `pyproject.toml` and CI.

It aligns with **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** (**Explicit contracts**, **Consumer-side maintenance**, **Observable automation**): supported versions are documented, pins and shims live in this repository, and automation must show what was exercised.

## 1. Purpose

- **Maintainers** upgrade replayt and OpenTelemetry **deliberately**, with documented rationale for bounds.
- **Integrators** see which upstream lines are **supported** vs merely **installable** by resolver luck.
- **CI** proves that claimed cells of the matrix pass **Ruff** and **pytest** (same commands as today unless the project explicitly changes them).

## 2. Human-readable matrix (README or docs)

### 2.1 Location

At least one of:

- The root **[README.md](../README.md)** **Version compatibility** section, **or**
- This document (with README linking here as the canonical table).

The matrix MUST be reachable from README without reading source code.

### 2.2 Table shape (normative)

The published matrix MUST include **one row per logical dependency** this package declares for replayt and OpenTelemetry **runtime** use:

| Column | Content |
| ------ | ------- |
| **Component** | Human-readable name (e.g. `replayt`, `OpenTelemetry API`, `OpenTelemetry SDK`). |
| **Supported range** | The **same** specifiers as in `[project.dependencies]` in `pyproject.toml` (or a clearly equivalent summary, e.g. “see `pyproject.toml`” only if the table is adjacent to a copy-paste of those lines). |
| **CI / validation** | How this row is validated: e.g. “default CI job”, “matrix job cell `replayt==x.y.z`”, or “documented only (not yet in matrix)” during transition—see **§4**. |
| **Notes** | Optional: reference replayt line used in examples, OTel major policy, link to CHANGELOG entry when bounds change. |

Optional rows for **`[project.optional-dependencies]`** (e.g. OTLP HTTP extra) SHOULD appear when integrators routinely need alignment (same OTel major as API/SDK).

### 2.3 Consistency rule

When `[project.dependencies]` (or optional extras) change in a release branch, **the matrix and [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §7.3 snapshot MUST be updated in the same change** (or the same PR), so integrators never see contradictory bounds.

## 3. `pyproject.toml` bounds and justification

### 3.1 What must be declared

Runtime dependencies that touch the integration boundary MUST remain explicit in `[project.dependencies]`:

- `replayt`
- `opentelemetry-api`
- `opentelemetry-sdk`

(Plus any other runtime deps the package adds for the same boundary.)

### 3.2 Justification (normative)

Every **lower** and **upper** bound (or cap) on those dependencies MUST have **documented rationale** in this repository, in at least one of:

- **[CHANGELOG.md](../CHANGELOG.md)** (**Unreleased** or release section), **or**
- This document (**§5 maintenance log** or inline notes next to the matrix), **or**
- A short subsection in README **Version compatibility**.

Rationale examples: “minimum replayt version that exposes `RunContext` used in tests,” “cap below 2.0 until OTLP semantic convention migration is tested,” “lower bound matches OpenTelemetry Python 1.20 tracing APIs we call.”

### 3.3 Upper bounds policy

- **replayt:** Upper bounds are **allowed and encouraged** once a breaking replayt release is known or to narrow the support claim to tested lines. Until then, a lower bound only is acceptable if README and this spec **explicitly** state that **latest satisfying the lower bound** is what CI exercises (current single-job behavior).
- **OpenTelemetry:** Stay on a **single supported major** per release unless CHANGELOG documents a major bump and matrix coverage. Upper caps (e.g. `<2`) MAY be used to avoid surprise major upgrades before validation.

### 3.4 Optional OTLP extra

If `[project.optional-dependencies].otlp` pins `opentelemetry-exporter-otlp-proto-http`, its bounds SHOULD be justified with the same OTel major/minor story as API/SDK.

## 4. How matrix updates are validated (CI and docs)

### 4.1 Implemented matrix (current)

**[.github/workflows/ci.yml](../.github/workflows/ci.yml)** job **`test`** (Python **3.12**) uses **`strategy.matrix`** with four cells: **replayt** pinned to **0.4.0** or **latest** (upgrade reinstall), crossed with **OpenTelemetry** **1.20.0** and **1.40.0** (API and SDK forced to the same version per cell). After `pip install -e ".[dev]"`, the workflow reapplies those pins, runs **Print resolved dependency versions** (`importlib.metadata.version` for `replayt`, `opentelemetry-api`, `opentelemetry-sdk`), then **Ruff** and **pytest**—same commands as a single-job baseline.

### 4.2 Target state (Builder obligation) — satisfied

The backlog automation obligations are met when items **1–3** below hold (this repository matches them as of phase **3**):

1. **CI uses a `strategy.matrix`** (or equivalent) that runs **pytest** (and the same Ruff steps as today) for **each** claimed combination of:
   - **replayt** version pins (at least **minimum** supported and **latest** or **representative** lines as defined in this spec), and
   - **OpenTelemetry** `opentelemetry-api` / `opentelemetry-sdk` pins aligned with the supported range (at least **minimum** and a **current** patch/minor on the supported major, unless a single pin is documented as sufficient).
2. Each matrix job **logs** resolved versions for `replayt`, `opentelemetry-api`, and `opentelemetry-sdk` (for example via `importlib.metadata.version`) so logs are auditable.
3. **README** and this document **name the workflow file** and the job id(s) that implement the matrix, and summarize what dimensions are covered (e.g. “replayt 0.4.x min + latest; OTel 1.20.x + 1.x latest”).

Python version dimension: if `[project].requires-python` allows multiple minors, policy SHOULD state whether CI matrices multiple Python versions or only documents one; today CI uses **3.12** only—any expansion MUST be documented here and in README.

### 4.3 Local reproduction

Contributors MUST be able to approximate a matrix cell locally, e.g. `pip install "replayt==…" "opentelemetry-api==…" "opentelemetry-sdk==…"` then `pytest`. README **Running tests** MAY add one sentence pointing to this section.

## 5. Maintenance log (optional template)

Maintainers MAY append dated rows when changing bounds:

| Date | Change | Rationale | Validated by |
| ---- | ------ | --------- | ------------ |
| 2026-03-28 | `replayt` lower bound `>=0.4.0`; OTel API/SDK OTLP extra `>=1.20.0,<2` | Tests and `tracing.py` map `RunFailed`, `ContextSchemaError`, and related replayt types; cap OTel below 2 until a validated major bump | `.github/workflows/ci.yml` `test` matrix cells + [CHANGELOG.md](../CHANGELOG.md) **Unreleased** |

## 6. Acceptance criteria summary

| Phase | Criterion |
| ----- | --------- |
| **Spec (phase 2)** | This document exists; [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §7 and README link here; backlog mapping appears in PUBLIC_API_SPEC §1.1; CHANGELOG **Unreleased** notes the spec. |
| **Builder (phase 3+)** | Matrix table populated per **§2**; `pyproject.toml` bounds match table; justifications per **§3**; CI matrix per **§4.2**; CHANGELOG records dependency-facing changes. |

## 7. Related documents

- [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) — §7 version snapshot; public API and seam.
- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) — explicit contracts and consumer-side maintenance.
- [CHANGELOG.md](../CHANGELOG.md) — release-facing dependency and validation notes.
