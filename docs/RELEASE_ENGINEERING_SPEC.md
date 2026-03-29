# Release engineering: PyPI publish and version sync

This document is the **specification** for backlog item *Release engineering: PyPI publish and version sync*. It turns the backlog into **testable obligations** for maintainers and for the **Builder** phase that wires **automation**, **`pyproject.toml`**, package **`__version__`**, and **[CHANGELOG.md](../CHANGELOG.md)** so published artifacts do not drift from documented history.

It aligns with **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** (**Explicit contracts**, **Observable automation**): releases MUST be **repeatable**, **auditable**, and MUST NOT rely on **long-lived PyPI credentials** in the repository when **trusted publishing** is available.

## 1. Purpose

- **Maintainers** cut releases with a **single, documented checklist** (changelog, version, tag, build, upload) and clear **ownership** of which file is canonical for the distribution version.
- **Integrators** see a **PyPI version** that matches **CHANGELOG** and **`__version__`** (no “Unreleased” features shipped under an old number).
- **Security / ops** prefer **OIDC trusted publishing** from GitHub Actions over stored API tokens.

## 2. Current state (facts for Builder)

After Builder phase **3** (release engineering implementation):

- **`[project].version`** in **`pyproject.toml`** is the **only** version **literal** (strategy **B** — **§6.1**).
- **`replayt_opentelemetry_exporter.__version__`** is set at import time via **`importlib.metadata.version("replayt-opentelemetry-exporter")`** (same value as **`[project].version`** when the distribution is installed).
- **`tests/test_version_sync.py`** asserts **`pyproject.toml`**, **`importlib.metadata`**, and **`__version__`** stay aligned (**§6.4**).
- **Tag-gated** publish workflow: [`.github/workflows/publish-pypi.yml`](../.github/workflows/publish-pypi.yml) (**§5.2**), including **`twine check dist/*`** after **`python -m build`** (same **§5.1** gate as local releases).

Historical note (spec time before Builder): **`[project].version`** and **`__init__.py`** both duplicated **`0.1.0`** while **[CHANGELOG.md](../CHANGELOG.md)** accumulated **`[Unreleased]`** work; that drift was resolved by cutting **`[0.2.0]`** and adopting strategy **B**.

## 3. Backlog acceptance mapping

The backlog item *Release engineering: PyPI publish and version sync* is satisfied when:

| Backlog acceptance criterion | Normative requirement in this spec |
| ---------------------------- | ---------------------------------- |
| **Repeatable release checklist** (tag, build wheel/sdist, twine upload) | **§4** — ordered maintainer checklist; **§5** — local build and `twine check` / upload commands (automation MAY supersede manual upload). |
| **Single source of truth** for **`__version__`** (optional hatch / setuptools-scm) | **§6** — pick **exactly one** version strategy; document it in README **Releases** (or equivalent) and here; **forbid** silent mismatch between strategy outputs. |
| **GHA workflow** gated on **tag** with **trusted publishing** | **§5.2** — sketch and Builder checklist; OIDC + `pypa/gh-action-pypi-publish` (or documented successor); **no** PyPI password secret in repo for the default path. |
| **No accidental drift** between **CHANGELOG** and **`__version__`** / distribution version | **§6.3**, **§7** — release-time rules; optional **§6.4** automation hook for Builder. |

### 3.1 Backlog: *Ship first PyPI release and document version / upgrade policy*

The backlog item *Ship first PyPI release and document version / upgrade policy* is satisfied when the following normative material exists and stays aligned (documentation is **Spec**; **PyPI upload** and **tag** are **maintainer / Builder** execution):

| Backlog theme | Normative location |
| ------------- | ------------------ |
| **Version bump**, **tag**, **PyPI** publish path (workflow or equivalent) | **§4**–**§5.2**, **§6**–**§6.3**; **`.github/workflows/publish-pypi.yml`**; README **Releases and PyPI** |
| **CHANGELOG** sections match the shipped version (no stale **Unreleased**-only story for released work) | **§6.3**; **§9.2**; [CHANGELOG.md](../CHANGELOG.md) |
| **Integrator** guidance: **pinning**, **SemVer** for **this** adapter, **breaking** expectations for **`__all__`** and **metric / trace names** | [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§7.6**, **§3**, **§5.7**, **§6.8**; README **Pinning, SemVer, and breaking changes** |

**Fact note:** The repository may already ship **`[project].version` 0.2.0** and automation from the *Release engineering: PyPI publish and version sync* backlog; this backlog still **requires** explicit integrator-facing **upgrade policy** prose (README + **§7.6**) and a **verifiable** first consumer line on **PyPI** matching **§9.1** (**0.2.0** vs scaffold **0.1.0**).

## 4. Maintainer release checklist (normative)

Before **any** PyPI release of **`replayt-opentelemetry-exporter`**, maintainers MUST follow this order unless a later revision of this spec documents a **narrower** automation that makes a step redundant (e.g. fully automated changelog — **not** required by this backlog):

1. **Green mainline** — Default branch (or documented release branch) passes **[CI_SPEC.md](CI_SPEC.md)** job **`test`** (and any other **README-listed** required checks).
2. **Changelog** — Move content from **`[Unreleased]`** into a new **`[X.Y.Z] - YYYY-MM-DD`** section (Keep a Changelog style). The **`X.Y.Z`** MUST equal the **version being released** (see **§6**). The new section MUST describe **user-visible** changes for that version (documentation-only releases are allowed; say so explicitly when applicable).
3. **Version bump** — Apply **§6** so **`pyproject.toml`**, runtime **`__version__`** (if present), and the **tag** all match **`X.Y.Z`**.
4. **Merge** — Land the changelog + version bump on the branch that **tags** are cut from (default: **`master`**, or document otherwise in README **Releases**).
5. **Tag** — Create an **annotated** or **lightweight** git tag per **§6.2** (documented convention). **Tag name MUST map unambiguously** to **`X.Y.Z`** (see **§6.2**).
6. **Build artifacts** — Produce **wheel** and **sdist** with **`python -m build`** (PEP 517) from a **clean** checkout at the tagged commit; outputs under **`dist/`** (or documented path).
7. **Validate distributions** — Run **`twine check dist/*`** (or documented equivalent) before upload; fix **README/metadata** issues **before** publishing.
8. **Publish** — Upload to **PyPI** via **§5.2** (preferred) or **`twine upload`** with **short-lived** credentials outside CI (discouraged for routine releases once trusted publishing exists).

## 5. Build, check, and publish

### 5.1 Local commands (reference)

From the repository root, after installing build tooling (Builder SHOULD document **`[dev]`** or **`build`/`twine`** install path in README **Releases**):

```bash
python -m build
twine check dist/*
```

**Normative:** **`python -m build`** is the **standard** build entry point; **`twine check`** MUST pass before **any** upload.

### 5.2 GitHub Actions sketch (tag-gated, trusted publishing)

Builder MUST add a **separate** workflow file (name is **Builder’s choice**, but README **Releases** MUST link to it) with **at least** the following **intent** (exact YAML is **Builder** work):

| Element | Requirement |
| ------- | ----------- |
| **Trigger** | **`push`** of **version tags** only (see **§6.2**), **not** every PR — publishing MUST NOT run on ordinary branch pushes unless this spec is explicitly revised. |
| **Permissions** | **`id-token: write`** for **OIDC** to PyPI; **`contents: read`** (or **read** + **attestations** if using **artifact attestations** — optional). **Do not** grant **`contents: write`** solely for publish unless justified elsewhere. |
| **Steps (logical)** | Checkout at the tag; set up Python; install **`build`**; run **`python -m build`**; upload with **`pypa/gh-action-pypi-publish`** (pinned version) using **PyPI **trusted publisher** configuration** for this repository — **no** `PYPI_API_TOKEN` in **repository secrets** for the **default** path. |
| **Concurrency** | **Optional but recommended:** concurrency group or **environment** protection so **double-tag** retries do not race. |
| **Test PyPI** | **Optional:** separate workflow or `environment` for **TestPyPI** with distinct trusted publisher; document in README if provided. |

**Operational note (informative):** PyPI **trusted publishing** is configured **in the PyPI project settings** (link GitHub repo + workflow + environment). This spec does not duplicate PyPI UI steps; README **Releases** SHOULD link to **PyPA** / **PyPI** docs for first-time setup.

### 5.3 Relationship to [CI_SPEC.md](CI_SPEC.md)

- **PR CI** (`.github/workflows/ci.yml` **job `test`**) remains the **quality gate** for merges.
- **Publish workflow** MAY use **different** permissions (**`id-token: write`**) and MUST NOT weaken **§3.3** of [CI_SPEC.md](CI_SPEC.md) on **existing** jobs (no secret dumps, minimal permissions on **`test`**).

Cross-link: [CI_SPEC.md](CI_SPEC.md) **§6** lists related documents including this spec.

## 6. Single source of truth for the distribution version

### 6.1 Choose one strategy (normative)

Builder MUST implement **exactly one** of the following (document the choice in README **Releases** and keep **§2** of this document accurate after implementation):

| Strategy | Canonical version lives in | `__version__` in code |
| -------- | -------------------------- | ---------------------- |
| **A — Static dual sync** | **`[project].version`** in **`pyproject.toml`** | **Same string literal** in **`__init__.py`** (current pattern, but MUST be **guarded** against drift — **§6.4**). |
| **B — Dynamic from metadata** | **`[project].version`** in **`pyproject.toml`** only | **`__version__`** is **read at import time** via **`importlib.metadata.version("replayt-opentelemetry-exporter")`** (or equivalent) so **one** literal exists. **§3** of [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) still exports **`__version__`**. |
| **C — Tag-driven (hatch-vcs / setuptools-scm)** | **Git tag** drives **`[project].version`** dynamically | **`__version__`** MAY be supplied by the build backend / template — MUST match **published** metadata; document **tag format** (**§6.2**). |

**Optional tooling** (hatch, setuptools-scm) is **allowed** under strategy **C**; strategy **B** avoids extra build backends if maintainers accept **`importlib.metadata`** at runtime.

### 6.2 Tag format (normative)

- **Default:** tags **`vMAJOR.MINOR.PATCH`** (example: **`v0.2.0`**) map to version **`MAJOR.MINOR.PATCH`**.
- If the project adopts **tags without `v`**, README and this spec MUST state that explicitly **and** the **publish workflow** filter MUST match the chosen pattern.
- **Pre-releases** (e.g. **`v1.0.0rc1`**) MUST use **PEP 440**-compatible forms and MUST be **documented** in README if used.

### 6.3 Changelog alignment (normative)

- The **topmost released** section in **[CHANGELOG.md](../CHANGELOG.md)** after a release MUST be **`[X.Y.Z]`** matching **PyPI** and **`__version__`**.
- **`[Unreleased]`** MUST **not** claim shipped work that is **not** yet on **PyPI** under a **released** version — i.e. after release, remaining bullets stay under **`[Unreleased]`** for the **next** cycle.
- **Keep a Changelog** section ordering and **SemVer** claims remain project policy; this spec requires **consistency**, not a rewrite of historical entries.

### 6.4 Drift prevention (Builder SHOULD)

Builder SHOULD add **at least one** guardrail appropriate to strategy **A** / **B** / **C**, for example:

- **pytest** that asserts **`importlib.metadata.version("replayt-opentelemetry-exporter")`** equals **`replayt_opentelemetry_exporter.__version__`** and matches **`[project].version`** in **`pyproject.toml`** (exact strategy depends on **§6.1**); and/or
- **pre-commit** or **CI** step on **PRs** that compares literals when strategy **A** is chosen.

Exact test placement is **[TESTING_SPEC.md](TESTING_SPEC.md)** / Builder discretion; this spec **requires** the **behavior** (no silent drift), not a specific file name.

## 7. Builder acceptance checklist

The **implementation** backlog for *Release engineering: PyPI publish and version sync* (and the overlapping *Ship first PyPI release and document version / upgrade policy* documentation obligations in **§3.1**) is complete when:

1. **§6.1** — One version strategy is **implemented** and **documented** in README **Releases** (and **§2** here updated if facts change).
2. **§4** — Maintainer checklist is **reachable** from README (link to **this spec** or a README section that **reproduces** the checklist without contradiction).
3. **§5.1–§5.2** — **`python -m build`** + **`twine check`** documented; **tag-triggered** workflow exists and uses **trusted publishing** (**OIDC**) without **default** long-lived PyPI token in repo secrets.
4. **§6.2–§6.3** — Tag convention and **CHANGELOG** rules are **documented** and **satisfied** for the **first** release cut under the new process (may be a **patch** that **only** fixes versioning/docs if needed).
5. **§6.4** — Drift guardrail **shipped** or **explicitly waived** in a tracked doc (waive only with maintainer rationale — default: **do not waive**).
6. **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §8** items **13** and **17** pass in review alongside this document (**§3.1** integrator policy).

## 8. Related documents

- [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§3**, **§7.3**, **§8** — public **`__version__`**, release snapshot table, Builder checklist item **13**, checklist items **7** and **16** vs **§9** below.
- [CI_SPEC.md](CI_SPEC.md) — PR CI permissions and log hygiene vs publish workflow.
- [CHANGELOG.md](../CHANGELOG.md) — release notes discipline.
- [README.md](../README.md) — maintainer **Releases** entry point.
- [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) — external reference for OIDC setup (informative).

## 9. Integrator release hygiene (changelog, README, milestones)

Normative expectations for **CHANGELOG** cuts, **README** accuracy at ship time, **Upgrading** notes, and optional **GitHub** milestone policy. Cross-check **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §8** items **7** and **16** in review.

### 9.1 Definitions

- **Dated CHANGELOG section** — A **`[X.Y.Z] - YYYY-MM-DD`** block in **[CHANGELOG.md](../CHANGELOG.md)** for a released **PyPI** version **X.Y.Z**.
- **`[Unreleased]`** — Notes for work merged to the release branch that is **not** yet part of a dated section.
- **0.1.0 line** — **PyPI** **0.1.0** was **scaffolding** (packaging and placeholders) and did **not** ship the stable exporter API in **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §3** or the tracing and metrics contract in **§5–§6**. Upgrades from **0.1.0** to **0.2.0** follow **§9.2.4** as **adoption**, not a rename migration, unless a maintainer note documents otherwise.

### 9.2 Maintainer obligations when cutting a PyPI release

When publishing **X.Y.Z** to **PyPI**, maintainers MUST satisfy **§4**, **§6.3**, and the following:

1. **§9.2.1 — CHANGELOG cut** — The new **`[X.Y.Z]`** section contains the user-visible items for that release (moved from **`[Unreleased]`** as appropriate). After **X.Y.Z** is on **PyPI**, **`[Unreleased]`** MUST NOT duplicate bullets that belong only to **X.Y.Z**.

2. **§9.2.2 — Summary and compare** — The dated section MUST include a short summary for integrators and a **verifiable delta** (for example a **GitHub** compare URL from the previous release tag to **`vX.Y.Z`**, or an equivalent release-page link).

3. **§9.2.3 — README vs shipped behavior** — README tracing, metrics, and wiring instructions MUST match **PUBLIC_API_SPEC.md** **§5–§6** and the implementation at **`[project].version` X.Y.Z** under **`src/`**. Integrators SHOULD read the **dated** CHANGELOG section for their installed version and treat **`[Unreleased]`** as unreleased mainline work only.

4. **§9.2.4 — Upgrading / migration** — If the previous **PyPI** release exposed a different public surface (instrument names, lifecycle strings, required setup), the **`[X.Y.Z]`** section MUST include **Upgrading from …** notes or link to them. When the prior line did not ship the current metrics or events (**§9.1**), state **adoption** and document **rename** steps only when they apply.

5. **Version consistency** — **`[project].version`**, git **tag**, distribution metadata, runtime **`__version__`** (per **§6**), and the CHANGELOG **`[X.Y.Z]`** header MUST all match **X.Y.Z**.

### 9.3 GitHub milestones and projects

Repositories **MAY** use **GitHub Milestones** or **Projects** for release buckets. If this repository does **not** use them that way, README **Releases** (or maintainer docs) SHOULD record **N/A** for **§9.3** so integrators do not expect milestone artifacts.

### 9.4 Review acceptance table

Reviewers MAY verify a target release against:

| Check | Expectation |
| ----- | ----------- |
| **§9.2.1** | Dated section complete; **Unreleased** does not duplicate shipped **X.Y.Z** notes |
| **§9.2.2** | Summary plus compare link or equivalent |
| **§9.2.3** | README and **PUBLIC_API_SPEC.md** **§5–§6** match **`src/`** at **X.Y.Z** |
| **§9.2.4** | **Upgrading** / adoption vs rename when the prior line differs |
| **§9.3** | Milestone policy documented or **N/A** |
| **§9.2** (item **5**) | Version literals and CHANGELOG header agree (**§6**, **§6.3**) |
