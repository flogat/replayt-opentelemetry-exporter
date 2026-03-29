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

## 4. Where this spec sits in the doc set

| Document | Role |
| -------- | ---- |
| [TESTING_SPEC.md](TESTING_SPEC.md) | What pytest must prove; local vs CI parity for **tests**. |
| [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) | Matrix dimensions, pins, and **which** dependency versions each cell exercises. **OpenTelemetry 2.x** cells are **forbidden** until that spec **§7** (spike, docs, gating) is satisfied—expand the workflow only after those obligations are met. |
| **This document** | **How** CI presents commands, steps, exit codes, and safe logs for Ruff + pytest. |

## 5. Builder acceptance checklist

The **implementation** backlog for *Add CI with ruff, tests, and readable logs* is complete when:

1. **§3.1** — Job **`test`** (or successor) runs Ruff lint, Ruff format check, then pytest per matrix cell that claims full validation.
2. **§3.2** — Failed runs show a **step name** that identifies Ruff vs format vs tests; tools’ **non-zero exits** fail the job.
3. **§3.3–§3.4** — No deliberate secret dumps; permissions and logging follow the constraints above.
4. **§3.5** — README satisfies the entry-point and link requirements; **local Ruff invocations** in README match CI’s path set (or README explicitly states equivalent `ruff check .` / `ruff format --check .` when `[tool.ruff]` makes that equivalent).
5. [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) **Observable automation** remains satisfied in review (clear logs, meaningful exit codes).

## 6. Related documents

- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) — **Observable automation**.
- [TESTING_SPEC.md](TESTING_SPEC.md) — pytest commands and CI parity for **test behavior**.
- [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) — matrix and pins.
- [README.md](../README.md) — contributor commands and CI pointer.
- [CHANGELOG.md](../CHANGELOG.md) — release-facing notes when CI behavior or commands change.
