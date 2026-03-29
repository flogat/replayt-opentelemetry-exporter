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

Optional rows for **`[project.optional-dependencies]`** (for example OTLP **HTTP** `[otlp]` and OTLP **gRPC** `[otlp-grpc]`—see **§3.4**) SHOULD appear when integrators routinely need alignment (same OpenTelemetry major as API/SDK).

### 2.3 Consistency rule

When `[project.dependencies]` (or optional extras) change in a release branch, **the matrix and [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §7.3 snapshot MUST be updated in the same change** (or the same PR), so integrators never see contradictory bounds. When **§4.1** replayt pins or policy change, refresh **`docs/reference-documentation/`** version stamps in the same change set (or a follow-up docs PR) per **[REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md) §4.3**.

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
- **OpenTelemetry:** Stay on a **single supported major** per release unless CHANGELOG documents a major bump and matrix coverage. Upper caps (e.g. `<2`) MAY be used to avoid surprise major upgrades before validation. **OpenTelemetry 2.x** is governed by **§7** until this package explicitly supports it or documents a permanent exclusion with rationale.

### 3.4 Optional OTLP extras (`[otlp]` HTTP and `[otlp-grpc]` gRPC)

**Backlog:** *Add optional `[otlp-grpc]` extra and README example for gRPC exporters* — normative detail and acceptance mapping: **§6** (this document), [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§1.1** / **§8** item **18**, [CI_SPEC.md](CI_SPEC.md) **§2.3**, [TESTING_SPEC.md](TESTING_SPEC.md) **§4.6** (pyproject bound checks).

#### 3.4.1 `[otlp]` (HTTP)

If `[project.optional-dependencies].otlp` pins `opentelemetry-exporter-otlp-proto-http`, its bounds SHOULD be justified with the same OpenTelemetry major/minor story as API/SDK (today: **`>=1.20.0,<2`**, mirroring `[project.dependencies]` for API/SDK).

#### 3.4.2 `[otlp-grpc]` (gRPC) — Builder obligation

The distribution MUST declare **`[project.optional-dependencies].otlp-grpc`** (PEP 621 extra key: `otlp-grpc`) listing **`opentelemetry-exporter-otlp-proto-grpc`** with **the same version specifiers** as the HTTP extra (**character-for-character equality** of the requirement string to **`opentelemetry-exporter-otlp-proto-http`** in **`[otlp]`**, unless a single shared constraint is refactored in `pyproject.toml` and both extras reference it—either way, resolved bounds for the two exporter packages MUST stay aligned on the **1.x** / **`<2`** line until [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7** allows otherwise).

**Rationale (for README matrix or **§5**):** gRPC is a common production transport for OTLP collectors and meshes; shipping a pinned extra avoids integrators guessing a compatible exporter line next to this package’s API/SDK range.

#### 3.4.3 README and operator guidance (HTTP vs gRPC)

The root **[README.md](../README.md)** MUST, in addition to the existing OTLP HTTP walk-through:

1. **Install** — Document `pip install -e ".[dev,otlp-grpc]"` (or `replayt-opentelemetry-exporter[otlp-grpc]` for integrators) alongside **`[otlp]`**, and state that integrators normally choose **one** transport extra unless they have a documented need for both.
2. **Minimal wiring** — Show **`install_tracer_provider`** and **`install_meter_provider`** with **`OTLPSpanExporter`** and **`OTLPMetricExporter`** imported from **`opentelemetry.exporter.otlp.proto.grpc`** (`trace_exporter` / `metric_exporter` submodules per OpenTelemetry Python’s public layout at the pinned version). The snippet MUST mirror the structure of the HTTP example in [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§3.3** (same adapter imports and provider install pattern; only exporter classes and install extra differ).
3. **Environment variables** — Document at least **`OTEL_EXPORTER_OTLP_ENDPOINT`** (and note trace- or metrics-specific endpoint variables when split). Mention **`OTEL_EXPORTER_OTLP_PROTOCOL`** / **`OTEL_EXPORTER_OTLP_TRACES_PROTOCOL`** / **`OTEL_EXPORTER_OTLP_METRICS_PROTOCOL`** where integrators must force **`grpc`** (or avoid HTTP/protobuf defaults) for their collector. Cross-link or one-line pointer to upstream OTLP exporter docs for full env reference.
4. **When to pick HTTP vs gRPC** — Short integrator-facing guidance (bullet list or paragraph): **HTTP** — typical behind **L7 load balancers**, restrictive proxies, and some serverless or gateway-only paths; **gRPC** — common with **Kubernetes** service meshes, some vendor collectors, and **HTTP/2**-native paths; **TLS / mTLS** — both transports support TLS; mTLS and corporate PKI details stay in OpenTelemetry and platform docs (README states that operators follow distro/collector guidance). This section satisfies the backlog’s “extend CI **or** docs” clause via **docs**; CI extensions are optional per **§3.4.4**.

#### 3.4.4 CI (optional)

The merge gate **MAY** remain unchanged (no new matrix rows) if **§3.4.3** and the README **Version compatibility** table row for **`[otlp-grpc]`** ship together. **Optional** Builder hardening (pick **one** unless maintainers agree more):

- Add a **documentation** or **supply-chain** step that installs **`".[dev,otlp-grpc]"`** on **one** existing matrix cell and runs **`import opentelemetry.exporter.otlp.proto.grpc`** (or a tiny smoke script) **without** adding network-backed export tests, **or**
- Extend **`tests/test_pyproject_dependencies.py`** (or successor) so **`[otlp-grpc]`** bounds are asserted like **`[otlp]`** today (recommended minimum—keeps pins honest without new workflow rows).

Network integration tests against a real collector are **out of scope** for this backlog unless a future spec explicitly requires them.

## 4. How matrix updates are validated (CI and docs)

### 4.1 Merge gate matrix (normative — requires-python parity)

**Declared:** `[project].requires-python` is **`>=3.11`** (`pyproject.toml`). **Tested (merge-blocking):** CI MUST run the **full** replayt×OpenTelemetry cell set on **Python 3.11** and on **Python 3.12** on every **`push` / `pull_request`** path that gates merges (today: job **`test`** in **[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)**). That is **requires-python parity**: the declared **minimum** minor (**3.11**) is not weaker than what the merge gate exercises.

**Cell set (replayt × OpenTelemetry — same on each Python minor):** **`strategy.matrix`** (or equivalent, e.g. `matrix.include`) with four combinations: **replayt** **0.4.0** or **latest** (upgrade reinstall), crossed with **OpenTelemetry** **1.20.0** and **1.40.0** (API and SDK forced to the same version per row). **Total merge-blocking rows:** **8** (2 Python minors × 4 dependency cells).

**Per row:** After `pip install -e ".[dev]"`, reapply pins for that row, run **Print resolved dependency versions** (`importlib.metadata.version` for `replayt`, `opentelemetry-api`, `opentelemetry-sdk`), then **Ruff** lint, **Ruff** format check, and **`pytest -q`**—exact invocations and step boundaries are **[CI_SPEC.md](CI_SPEC.md) §3.1** (CLI `ruff …` vs `python -m ruff …` MUST stay equivalent). **`[tool.ruff]` `target-version`** (currently **py311**) already aligns Ruff with the **3.11** floor; CI MUST still run Ruff on the **same** `src`/`tests` path set documented in README.

### 4.2 Target state (Builder obligation) — satisfied for OpenTelemetry 1.x

The backlog automation obligations for the **1.x** line are met when items **1–4** below hold (this repository matches them as of phase **3** for **OpenTelemetry API/SDK 1.x**):

1. **CI uses a `strategy.matrix`** (or equivalent) that runs **pytest** (and the same Ruff steps as today) for **each** claimed combination of:
   - **Python** minors that match **§4.1** (currently **3.11** and **3.12** on the merge gate),
   - **replayt** version pins (at least **minimum** supported and **latest** or **representative** lines as defined in this spec), and
   - **OpenTelemetry** `opentelemetry-api` / `opentelemetry-sdk` pins aligned with the supported range (at least **minimum** and a **current** patch/minor on the supported major, unless a single pin is documented as sufficient).
2. Each matrix job **logs** resolved versions for `replayt`, `opentelemetry-api`, and `opentelemetry-sdk` (for example via `importlib.metadata.version`) so logs are auditable.
3. **README** and this document **name the workflow file** and the job id(s) that implement the matrix, and summarize what dimensions are covered (e.g. “Python 3.11 + 3.12; replayt 0.4.x min + latest; OTel 1.20.x + 1.40.x”).
4. **Declared vs tested** for Python is explicit in README **Version compatibility** (and here): **`requires-python`** vs which minors run the **full** cell set on PR.

**OpenTelemetry 2.x:** Do **not** add CI matrix cells for 2.x until **§7** is satisfied (spike validated, bounds justified, docs and optional extras aligned). Until then, the matrix exercises **1.x** pins only.

### 4.3 Historical transitional job (`test-python-3-11`) — removed when §4.1 shipped

Before **§4.1** parity landed in YAML, the repository used job **`test-python-3-11`** as a **partial** check on **3.11** (one pin set, **`schedule` + `workflow_dispatch`** only). That layout **did not** satisfy **requires-python parity** by itself. Builder work *Expand CI matrix to include Python 3.11 (requires-python parity)* extended job **`test`** to eight rows and **removed** **`test-python-3-11`** and the workflow **`schedule`** that existed only for it.

If maintainers ever reintroduce a second **3.11** story, amend this spec and README with an explicit rationale (discouraged).

To approximate a **single** matrix row locally on **3.11**, use Python **3.11**, `pip install -e ".[dev]"`, apply the desired replayt and OpenTelemetry pins for that row, then run the same Ruff and pytest commands as **[CI_SPEC.md](CI_SPEC.md) §3.1** and README **Running tests and lint locally**.

### 4.4 Local reproduction

Contributors MUST be able to approximate a matrix cell locally, e.g. `pip install "replayt==…" "opentelemetry-api==…" "opentelemetry-sdk==…"` then `pytest`. README **Running tests** MAY add one sentence pointing to this section.

## 5. Maintenance log (optional template)

Maintainers MAY append dated rows when changing bounds:

| Date | Change | Rationale | Validated by |
| ---- | ------ | --------- | ------------ |
| 2026-03-28 | `replayt` lower bound `>=0.4.0`; OTel API/SDK OTLP extra `>=1.20.0,<2` | Tests and `tracing.py` map `RunFailed`, `ContextSchemaError`, and related replayt types; cap OTel below 2 until a validated major bump | `.github/workflows/ci.yml` `test` matrix cells + [CHANGELOG.md](../CHANGELOG.md) **Unreleased** |
| 2026-03-29 | OpenTelemetry **2.x** explicit exclusion (unchanged `<2` cap) | PyPI had no `opentelemetry-api` / `opentelemetry-sdk` **2.x** (stable or `--pre`) at Builder audit; **§7.2** install blocked per step **0**; support deferred until published **2.x** and full spike | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7.2** audit paragraph; [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§7.4** |
| 2026-03-29 | Python **3.11** supplemental CI policy | `requires-python >=3.11` needs a non-PR-blocking smoke path; full replayt×OTel matrix stays on **3.12**; **3.11** smoke per **[CI_SPEC.md](CI_SPEC.md) §3.6** and **§4.3** here | Spec + Builder (*Expand CI matrix with optional Python 3.11 job*); README **Version compatibility** |
| 2026-03-29 | Job **`test-python-3-11`** in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | **§4.3** cell: **replayt** latest, OpenTelemetry API/SDK **1.40.0**, Python **3.11**; triggers **`schedule`** (weekly) and **`workflow_dispatch`** only (`if` on the job); same Ruff/pytest as **`test`** | Phase **3** builder (*Expand CI matrix with optional Python 3.11 job*); `tests/test_ci_workflow.py` |
| 2026-03-29 | **Requires-python parity** (spec) | Merge gate MUST run full replayt×OTel matrix on **3.11** and **3.12** (**§4.1**); transitional **`test-python-3-11`** documented in **§4.3** until Builder closes gap | Phase **2** spec (*Expand CI matrix to include Python 3.11 (requires-python parity)*); README **Version compatibility**; [CI_SPEC.md](CI_SPEC.md) **§2.2**, **§3.6** |
| 2026-03-29 | **Requires-python parity** (YAML) | Job **`test`**: eight rows (**3.11** / **3.12** × four replayt×OTel cells); removed **`test-python-3-11`** and **`on.schedule`** used only for it | Phase **3** builder (*Expand CI matrix to include Python 3.11 (requires-python parity)*); **`tests/test_ci_workflow.py`**; README **Version compatibility** |

## 6. Acceptance criteria summary

| Phase | Criterion |
| ----- | --------- |
| **Spec (phase 2)** — *Add compatibility matrix and dependency pins* | This document exists; [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §7 and README link here; backlog mapping appears in PUBLIC_API_SPEC §1.1; CHANGELOG **Unreleased** notes the spec. |
| **Spec (phase 2)** — *Validate OpenTelemetry 2.x and document policy* | **§7** (spike, documentation outcomes, CI gating); **§3.3** and **§4** reference **§7** where relevant; **§7.6** acceptance summary; [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§1.1** maps the backlog and **§7.4** states integrator-facing **1.x** / **2.x** policy; CHANGELOG **Unreleased** notes the spec pass. |
| **Spec (phase 2)** — *OpenTelemetry 2.x readiness spike (matrix branch + spec deltas)* | [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§1.1**, **§7.4.1** (touchpoint inventory), **§7.4.2** (go/no-go), **§8** item **12** cross-link; **§7.2** step **3** (findings artifact); **§7.5** (non-blocking automation); [CI_SPEC.md](CI_SPEC.md) **§2.4**; CHANGELOG **Unreleased** notes the spec pass. |
| **Spec (phase 2)** — *Expand CI matrix with optional Python 3.11 job* | Historical: merge-gate policy superseded by *Expand CI matrix to include Python 3.11 (requires-python parity)*; **§4.3** records the old supplemental job. |
| **Spec (phase 2)** — *Expand CI matrix to include Python 3.11 (requires-python parity)* | **§4.1** merge-blocking **3.11** + **3.12** × four replayt×OTel cells; **§4.2** item **4**; **§4.3** historical supplemental job; [CI_SPEC.md](CI_SPEC.md) **§2.2**, **§3.6**, **§5** items **6–7**; [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§1.1** / **§8** item **14**; README **Version compatibility** (**declared vs tested**); CHANGELOG **Unreleased** notes this spec pass. |
| **Spec (phase 2)** — *Add optional `[otlp-grpc]` extra and README example for gRPC exporters* | **§3.4** (extras, README content, optional CI); [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§1.1** / **§8** item **18**; [CI_SPEC.md](CI_SPEC.md) **§2.3**; [TESTING_SPEC.md](TESTING_SPEC.md) **§4.6**; CHANGELOG **Unreleased** notes this spec pass. |
| **Builder (phase 3+)** — matrix / pins backlog | Matrix table populated per **§2**; `pyproject.toml` bounds match table; justifications per **§3**; CI matrix per **§4.2**; CHANGELOG records dependency-facing changes. |
| **Builder (phase 3+)** — *Add optional `[otlp-grpc]` extra and README example for gRPC exporters* | **`[otlp-grpc]`** in `pyproject.toml` per **§3.4.2**; README **§3.4.3**; **Version compatibility** table row; [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§8** item **18**; bound check in **`tests/test_pyproject_dependencies.py`** per **§3.4.4**; optional CI/smoke per **§3.4.4**; CHANGELOG **Unreleased** when shipping. |
| **Builder (phase 3+)** — *Expand CI matrix to include Python 3.11 (requires-python parity)* | Job **`test`** implements **§4.1** (eight matrix rows); **`test-python-3-11`** removed per **§4.3**; README **CI / validation** column; **`tests/test_ci_workflow.py`**; Ruff + pytest match **[CI_SPEC.md](CI_SPEC.md) §3.1** and README; CHANGELOG **Unreleased** when behavior ships. |
| **Builder (phase 3+)** — *OpenTelemetry 2.x* | **§7.6** Builder row. |

## 7. OpenTelemetry 2.x validation, policy, and CI gating

This section is the **normative** contract for backlog item *Validate OpenTelemetry 2.x and document policy*. It applies to **`opentelemetry-api`**, **`opentelemetry-sdk`**, and the optional **`[otlp]`** / **`[otlp-grpc]`** extras (`opentelemetry-exporter-otlp-proto-http`, `opentelemetry-exporter-otlp-proto-grpc`), which MUST stay on the **same** supported OpenTelemetry major/minor story as API/SDK.

### 7.1 Current declared position (until a Builder changes it)

- **`pyproject.toml`** caps OpenTelemetry runtime dependencies **below 2** (`<2`) together with a lower bound (currently `>=1.20.0`). That cap means **OpenTelemetry Python 2.x is not a supported install target** for this package until the steps in **§7.3–7.4** complete.
- Integrators MUST treat **1.x within the declared range** as the supported line; **2.x** is **out of scope** for support claims until documentation and matrix explicitly say otherwise.

### 7.2 Spike workflow (Builder / maintainer)

Before widening bounds or adding matrix cells for **2.x**, maintainers MUST run a **spike** on a **branch** (not necessarily merged) that:

0. **Prerequisite — published packages:** If **no** `opentelemetry-api` / `opentelemetry-sdk` **2.x** release or pre-release is available on **PyPI**, the install step below is **blocked**. A **Builder** pass MUST still record that audit (tooling used, date, and outcome: no installable **2.x**) in this section or **§5**, keep the **`<2`** cap, and treat **§7.3** *explicit exclusion* as satisfied until **2.x** appears—then run steps **1–3** before claiming support.
1. **Installs** OpenTelemetry **2.x** for API and SDK (and, if validating export paths, the matching **2.x** OTLP **HTTP** and **gRPC** exporter versions when those extras are declared) using **published** packages—**pre-release** wheels are acceptable when **stable 2.x** is not yet on PyPI, provided the spike documents the exact versions used.
2. **Runs** the same quality gates this repository expects for a merge candidate: **Ruff** lint, **Ruff** format check, and **full `pytest`** from the repository root (same invocations as [CI_SPEC.md](CI_SPEC.md) **§3.1**), after reconciling any **code** changes required for API or semantic-convention differences.
3. **Records** findings in a **single maintainer-facing artifact** (PR description, section in this document, or linked doc under **`docs/`**—pick one and link it from **§5** when not inline):
   - A **table** mapping each touchpoint in [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§7.4.1** to **2.x** impact (**breaking** / **deprecated** / **unchanged** / **unknown**) with pointers to upstream release or migration notes.
   - Code locations beyond **`tracing.py`** if the spike reveals additional OpenTelemetry usage (tests, packaging, optional OTLP imports).
   - Test and Ruff outcomes on the spike branch at pinned **2.x** versions.
   - A explicit **go** / **no-go** / **defer** for widening **`<2`**, per [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§7.4.2** (the **no-go** or **defer** path still satisfies the spike backlog when documented—**shipping** widening requires **§7.3** *support* plus **§7.4** matrix rules).

The spike proves **feasibility**; **shipping** support still requires **§7.3–7.4**.

**Builder audit (phase 3, 2026-03-29):** `pip index versions opentelemetry-api` and `pip index versions opentelemetry-api --pre` on PyPI showed **no** **2.x** line for **`opentelemetry-api`** (latest **1.40.0**). The same constraint applies to **`opentelemetry-sdk`** (paired releases). No **2.x** install or Ruff/pytest spike was possible; this package remains **1.x**-only with **`>=1.20.0,<2`** until **2.x** packages exist and a maintainer repeats **§7.2** steps **1–3**.

**Automation (phase 3, 2026-03-29):** [`.github/workflows/otel-2x-spike.yml`](../.github/workflows/otel-2x-spike.yml) (job **`otel-2x-spike`**) implements **§7.5** / [CI_SPEC.md](CI_SPEC.md) **§2.4**: **`workflow_dispatch`** and weekly **`schedule`**, [`scripts/otel_2x_probe.py`](../scripts/otel_2x_probe.py) for a paired **2.x** pin, then **§3.1** checks when a pair exists; otherwise the job skips Ruff/pytest and stays green (**§7.2** step **0**).

### 7.3 Documentation outcomes (required before merge)

After the spike, the **merge** that claims **2.x** support (or the decision **not** to support it) MUST update **all** of the following **in the same change set** (or an explicitly linked docs PR that lands before dependency bounds merge):

| Outcome | Updates required |
| ------- | ---------------- |
| **Support 2.x** (range may include 1.x and 2.x or 2.x-only—decide explicitly) | `[project.dependencies]` and **`[otlp]`** / **`[otlp-grpc]`** bounds in `pyproject.toml`; **§2** matrix table and **§5** maintenance log row with rationale; [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§7** (including **§7.3** snapshot table); README **Version compatibility**; [CHANGELOG.md](../CHANGELOG.md) **Unreleased**; [TESTING_SPEC.md](TESTING_SPEC.md) **§4.6** expectations for bound checks. |
| **Explicit exclusion** (remain on **1.x** only for a release line) | This section or **§5** documents **why** (e.g. upstream instability, breaking SDK behavior not yet justified, or satellite bandwidth); [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§7** states integrators must not expect 2.x; README and **§2** matrix **CI / validation** column stay accurate (still **1.x**-only matrix). |

### 7.4 CI matrix expansion (after bounds are justified)

- **Do not** extend **`.github/workflows/ci.yml`** `strategy.matrix` (or equivalent) with OpenTelemetry **2.x** pins until **§7.2** spike passes **Ruff + pytest** on that branch **and** **§7.3** documentation is updated to match the chosen outcome.
- When **2.x** is supported, matrix cells MUST include at least **one** pinned **2.x** API/SDK pair (same version for both) in addition to existing **1.x** coverage **unless** this spec is amended to document a deliberate narrower claim (e.g. “2.x-only drop 1.x” in a semver-major release)—that amendment MUST appear in **§4.1** / **§2** and in [CHANGELOG.md](../CHANGELOG.md).
- Resolved-version logging (**§4.2** item 2) MUST include **`opentelemetry-api`** and **`opentelemetry-sdk`** for every **new** 2.x cell.

### 7.5 Non-merge-blocking OpenTelemetry 2.x automation (readiness spike)

Backlog *OpenTelemetry 2.x readiness spike (matrix branch + spec deltas)* allows **early signal** on **2.x** candidates **without** widening the PR **merge gate** before **§7.3–7.4** are satisfied.

- **Purpose** — Run **Ruff** + **full `pytest`** (same invocations as [CI_SPEC.md](CI_SPEC.md) **§3.1**) against a **pinned** **2.x** `opentelemetry-api` / `opentelemetry-sdk` pair (and matching OTLP extras if exercised) on **`workflow_dispatch`**, **`schedule`**, and/or **`pull_request`** with an explicit **`if`** / path filter so **failed** runs **do not** block merges—**or** document an equivalent **manual** branch procedure in **§7.2** findings when CI is deferred.
- **Forbidden until justified** — Treating **2.x** green runs as **supported** in README, **`pyproject.toml`**, or the **§4.1** merge matrix **without** **§7.3** documentation and **§7.4** matrix rules.
- **Naming** — Workflow or job id SHOULD name OpenTelemetry **2.x** explicitly (e.g. **`otel-2x-spike`**) so logs are auditable; see [CI_SPEC.md](CI_SPEC.md) **§2.4**.
- **Pins** — The workflow MUST print resolved **`opentelemetry-api`**, **`opentelemetry-sdk`**, and **`replayt`** versions for the row (same style as job **`test`**).
- **Repository workflow** — [`.github/workflows/otel-2x-spike.yml`](../.github/workflows/otel-2x-spike.yml) (**`otel-2x-spike`** job); README **Version compatibility** describes triggers and behavior.

### 7.6 Acceptance criteria summary (this backlog)

| Phase | Criterion |
| ----- | --------- |
| **Spec (phase 2)** | **§7** exists with spike workflow, documentation outcomes table, CI gating, and **§7.5** non-blocking **2.x** automation rules; **§3.3** references **§7**; [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§1.1** maps this backlog and the *readiness spike* backlog; **§7.4** / **§7.4.1–7.4.2** there state integrator policy, **`tracing.py`** touchpoints, and **go/no-go**; cross-links match [CI_SPEC.md](CI_SPEC.md) **§2.4**. |
| **Builder (phase 3+)** | **§7.2** satisfied: full spike (**1–3**) when **2.x** is on PyPI, **or** **§7.2** step **0** audit recorded when **2.x** is absent; **§7.3** satisfied for support or exclusion; if support: `pyproject.toml`, CI matrix per **§7.4**, README, CHANGELOG, and tests green on claimed bounds; if exclusion: docs and rationale per **§7.3** without widening `<2`. |

## 8. Related documents

- [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) — §7 version snapshot; public API and seam; OpenTelemetry 2.x policy cross-link.
- [REFERENCE_DOCUMENTATION_SPEC.md](REFERENCE_DOCUMENTATION_SPEC.md) — **`docs/reference-documentation/`** version-stamped snapshots; replayt lines MUST match **§4.1** pins.
- [TESTING_SPEC.md](TESTING_SPEC.md) — pytest commands, CI parity, **§4.6** dependency bound checks, and what the suite must prove at the replayt boundary.
- [CI_SPEC.md](CI_SPEC.md) — readable CI steps and safe logs for Ruff + pytest; matrix pins follow **§4** / **§7** here; **§2.4** for optional non-blocking **2.x** jobs.
- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) — explicit contracts and consumer-side maintenance.
- [CHANGELOG.md](../CHANGELOG.md) — release-facing dependency and validation notes.
