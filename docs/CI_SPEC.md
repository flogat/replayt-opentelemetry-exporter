# Continuous integration: Ruff, pytest, and readable automation

This document is the **specification** for backlog item *Add CI with ruff, tests, and readable logs*. It turns the backlog acceptance criteria into **testable obligations** for maintainers and for the **Builder** phase that edits [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) and contributor-facing docs.

It aligns with **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** (**Observable automation**): CI and local commands MUST surface **which tool failed**, use **standard process exit codes**, and avoid **noisy or secret-bearing log output**.

## 1. Purpose

- **Maintainers** bisect and review failures from **GitHub Actions** (or equivalent) without guessing which subprocess broke.
- **Contributors** run the **same** Ruff and pytest invocations locally as CI documents (see **§3** and [TESTING_SPEC.md](TESTING_SPEC.md) **§3**).
- **Security reviewers** see that automation does not echo credentials or unrelated secret material on failure paths.

## 2. Backlog acceptance mapping

The backlog item *Add CI with ruff, tests, and readable logs* is satisfied when:

| Backlog acceptance criterion | Normative requirement in this spec |
| ---------------------------- | ---------------------------------- |
| Workflow runs **ruff** (or documented equivalent) and **pytest** | **§3.1** — quality gate runs Ruff **lint**, Ruff **format check**, then **pytest** on every cell that claims full package validation (today: job **`test`** in `.github/workflows/ci.yml`). |
| Failed jobs surface **which command failed** without **noisy secret dumps** | **§3.2** (step boundaries and names), **§3.4** (logs and redaction expectations). |
| **README** links to or describes the CI entry point | **§3.5** — README names the workflow file and job(s) that run Ruff + pytest; **§4** points here as the normative contract. |

Other jobs in the same workflow file (for example **supply-chain** audits) are **out of scope** for this backlog unless README explicitly lists them as part of the “lint and tests” story.

### 2.2 Backlog — *Expand CI matrix to include Python 3.11 (requires-python parity)*

The backlog item *Expand CI matrix to include Python 3.11 (requires-python parity)* is satisfied when:

| Expectation | Normative requirement |
| ----------- | --------------------- |
| **Declared** Python floor matches **merge-gate** coverage | **`requires-python >=3.11`** implies the **full** replayt×OpenTelemetry matrix (see [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1**) runs on **3.11** **and** on **3.12** on **`push` / `pull_request`**—not only on **3.12**. |
| Same quality bar on every cell | **§3.1** — Each matrix row uses the **same** Ruff lint path set, Ruff format check path set, and **`pytest -q`** invocation after install + pins; **§3.2–§3.4** apply. |
| Contributor parity | There is no **`CONTRIBUTING.md`** in this repository; README **Running tests and lint locally** is the normative contributor surface. CI MUST stay aligned with those commands (including **`python -m ruff`** as the documented equivalent to the `ruff` CLI per **§3.1**). |

The earlier backlog *Expand CI matrix with optional Python 3.11 job* is **superseded** for merge-gate policy: a **`schedule`-only** supplemental job does **not** alone satisfy *requires-python parity* ([COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.3** describes the transitional layout until **§4.1** is implemented).

### 2.3 Backlog — *Add optional `[otlp-grpc]` extra and README example for gRPC exporters*

The backlog body asks to extend **CI or docs** for OTLP transport choice. Normative split:

| Expectation | Normative requirement |
| ----------- | --------------------- |
| **Minimum (merge gate unchanged)** | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§3.4.3** (README: HTTP vs gRPC, env vars, gRPC example) **fully satisfies** the “extend docs” path; **no** new **`test`** matrix rows are **required** for this backlog. |
| **Recommended test-side guard** | **`tests/test_pyproject_dependencies.py`** (or successor) asserts **`[otlp-grpc]`** pins mirror **`[otlp]`**—runs in existing cells without new install cost beyond editable **`[dev]`** if the test only reads `pyproject.toml`. |
| **Optional CI hardening** | [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§3.4.4**: one matrix cell **MAY** `pip install -e ".[dev,otlp-grpc]"` and run a **non-network** import or smoke step in a **separately named** workflow step so failures identify the optional extra (follow **§3.2** naming rules). |

If maintainers add an optional CI step, README **CI entry point** SHOULD mention it when it becomes part of the documented contributor story; default remains **§3.1** Ruff + pytest only.

### 2.4 Backlog — *OpenTelemetry 2.x readiness spike (matrix branch + spec deltas)*

Optional automation that exercises **OpenTelemetry Python 2.x** candidates is **normative** only as described in [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7.5**: it MUST **not** replace or gate the merge-blocking job **`test`** until **§7.3–7.4** there authorize **2.x** support.

| Expectation | Normative requirement |
| ----------- | --------------------- |
| **Non-blocking** | Workflow or job runs on **`workflow_dispatch`** and/or **`schedule`**, **or** on **`pull_request`** only when an explicit condition prevents it from being a **required** check (document the condition in README **Version compatibility** or **§7.2** findings). |
| **Commands** | Same **§3.1** order: install + pins, optional resolved-version print, **Ruff** lint, **Ruff** format check, **`pytest`** (full suite unless a narrower spike scope is documented with rationale in [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7.2** step **3**—default is **full** suite). |
| **Discoverability** | README or [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§7** names the workflow path and how maintainers trigger it. Implemented path: [`.github/workflows/otel-2x-spike.yml`](../.github/workflows/otel-2x-spike.yml) (**`otel-2x-spike`** job); README **Version compatibility** is canonical for triggers. |

## 3. Normative CI behavior

### 3.1 Commands (Ruff and pytest)

On each **matrix cell** (or single job) that validates the library:

1. **Install** — Editable install with dev extras (`pip install -e ".[dev]"` or documented equivalent), then apply any **documented** version pins per [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4**.
2. **Optional audit log** — Printing resolved versions of `replayt`, `opentelemetry-api`, and `opentelemetry-sdk` (for example via `importlib.metadata.version`) is **encouraged** for matrix auditability; such lines are not secrets.
3. **Ruff lint** — `ruff check` (or `python -m ruff check`) MUST run against at least the **`src/`** tree and the **`tests/`** tree (paths may be `src tests` or a documented equivalent such as `.` when **Ruff’s project config** clearly includes those trees—**README and CI MUST match**).
4. **Ruff format** — `ruff format --check` (or `python -m ruff format --check`) MUST use the **same path set** as the lint step.
5. **Pytest** — `pytest` MUST run from the **repository root** with the same **verbosity flags** CI documents (today: `pytest -q` in the workflow; README MAY show `pytest` without `-q` for local ergonomics provided **exit-code semantics** stay standard—see [TESTING_SPEC.md](TESTING_SPEC.md) **§3.3**).

**Documented equivalent** to the `ruff` CLI: invoking **`python -m ruff`** with the same subcommands and arguments, so environments without a `ruff` shim on `PATH` stay supported.

### 3.2 Step names and failure surfacing

- **One primary concern per step** for Ruff lint, Ruff format, and pytest: each MUST be its own workflow **step** (or an unmistakably named composite) so the GitHub Actions UI shows a **failed step title** that identifies the tool (e.g. **Ruff check**, **Ruff format**, **Run tests**).
- **Do not** fold unrelated commands into the same step as pytest in a way that hides whether Ruff or tests failed.
- **Exit codes** — Steps MUST **not** mask non-zero exits: no `|| true` on Ruff or pytest; no blanket `set +e` around the primary check unless documented and justified (default: **forbidden**).

### 3.3 Permissions and secrets

- Workflow **`permissions`** SHOULD stay **minimal** (for example `contents: read` only) unless a job needs more; document any expansion.
- **Do not** `echo` or print **`secrets.*`**, **`GITHUB_TOKEN`**, or other credential-bearing context variables in routine logs.
- **Do not** enable shell **xtrace** (`set -x`) for steps that run in environments where the platform might inject secret-like values into the environment in the future without a review.

### 3.4 Pip and build logs

- **Acceptable:** normal `pip install` resolver output, dependency names, and version pins.
- **Avoid:** dumping full environment files that might contain tokens; passing auth URLs with embedded credentials into `pip` in CI (use **OIDC** or **ephemeral secrets** patterns from GitHub docs if private indexes are ever required—out of scope for default public CI).

### 3.5 README and entry point

README MUST:

- Link to **`.github/workflows/ci.yml`** (or the repo’s canonical workflow path if renamed).
- State that **pull requests** (and **pushes** to tracked branches, if applicable) run **Ruff** and **pytest** as above.
- Link to **this spec** as the normative **CI readability and command** contract (see **§4**).

### 3.6 Python minor coverage (requires-python parity)

When `[project].requires-python` is **`>=3.11`** and maintainers also test a **newer** minor (today **3.12**):

1. **Merge gate** — Job **`test`** (or its successor) MUST exercise the **full** four-cell replayt×OpenTelemetry matrix on **Python 3.11** and on **Python 3.12** on every **`push` / `pull_request`** that gates merges—**eight** rows total unless this spec and [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1** are amended together. That satisfies **requires-python parity**: the declared **minimum** minor is covered by the same matrix depth as **3.12**.
2. **Ruff / pytest** — Each row runs **§3.1** commands (`ruff check src tests`, `ruff format --check src tests`, `pytest -q` in the workflow, equivalent to README’s **`python -m ruff …`**). **`[tool.ruff]` `target-version`** in `pyproject.toml` MUST remain consistent with the lowest merge-blocking minor (**py311** today).
3. **No duplicate Python story** — Do **not** add a second merge-adjacent **3.11** job that contradicts item **1** without updating [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.3** and README together. The historical **`test-python-3-11`** layout is documented there as **removed** once **§4.1** is satisfied in YAML.
4. **Resolved versions** — Every merge-blocking row SHOULD print resolved **`replayt`**, **`opentelemetry-api`**, and **`opentelemetry-sdk`** versions (same style as today’s **`test`** job).

## 4. Where this spec sits in the doc set

| Document | Role |
| -------- | ---- |
| [TESTING_SPEC.md](TESTING_SPEC.md) | What pytest must prove; local vs CI parity for **tests**. |
| [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) | Matrix dimensions, pins, and **which** dependency versions each cell exercises. **OpenTelemetry 2.x** merge-gate cells are **forbidden** until that spec **§7** (spike, docs, **§7.4** gating) is satisfied; optional **non-blocking** **2.x** jobs follow **§7.5** and **§2.4** here. |
| **This document** | **How** CI presents commands, steps, exit codes, and safe logs for Ruff + pytest. |

## 5. Builder acceptance checklist

The **implementation** backlog for *Add CI with ruff, tests, and readable logs* is complete when:

1. **§3.1** — Job **`test`** (or successor) runs Ruff lint, Ruff format check, then pytest per matrix cell that claims full validation.
2. **§3.2** — Failed runs show a **step name** that identifies Ruff vs format vs tests; tools’ **non-zero exits** fail the job.
3. **§3.3–§3.4** — No deliberate secret dumps; permissions and logging follow the constraints above.
4. **§3.5** — README satisfies the entry-point and link requirements; **local Ruff invocations** in README match CI’s path set (or README explicitly states equivalent `ruff check .` / `ruff format --check .` when `[tool.ruff]` makes that equivalent).
5. [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) **Observable automation** remains satisfied in review (clear logs, meaningful exit codes).
6. **§3.6** — Merge gate runs the **full** replayt×OpenTelemetry matrix on **Python 3.11** and **3.12** per [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.1**; Ruff and pytest invocations match **§3.1** and README on every row.
7. **§3.6** — Parity keeps a single **`test`** matrix story for **3.11** and **3.12**; any return of a supplemental **3.11**-only job needs an explicit spec + README rationale per [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) **§4.3**.

## 6. Related documents

- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) — **Observable automation**.
- [TESTING_SPEC.md](TESTING_SPEC.md) — pytest commands and CI parity for **test behavior**.
- [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) — matrix and pins; **§7.5** optional non-blocking **OpenTelemetry 2.x** jobs (**§2.4** here).
- [RELEASE_ENGINEERING_SPEC.md](RELEASE_ENGINEERING_SPEC.md) — **tag-gated** PyPI publish workflow (separate from this spec’s PR **`test`** job); **OIDC** permissions live on the publish workflow, not a reason to broaden **`test`** secrets.
- [README.md](../README.md) — contributor commands and CI pointer.
- [CHANGELOG.md](../CHANGELOG.md) — release-facing notes when CI behavior or commands change.
