# Reference documentation — replayt public surface (local snapshot)

This document is the **specification** for backlog item *Curate docs/reference-documentation from replayt public API*. It turns the backlog into **testable obligations** for the **Builder** phase that adds (or scripts) bounded markdown under **`docs/reference-documentation/`** and links from **[README.md](../README.md)** and **[REPLAYT_ECOSYSTEM_IDEA.md](REPLAYT_ECOSYSTEM_IDEA.md)**.

It aligns with **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** (**Explicit contracts**, **Consumer-side maintenance**, **Small public surfaces**): integrators get **local** context for the replayt symbols this adapter talks about, **version-stamped** to the same replayt lines the **compatibility matrix** exercises—without vendoring replayt or replacing upstream docs.

## 1. Purpose

- **Integrators** can read **bounded** descriptions of replayt’s **workflow/run** public API next to this package’s specs, offline and without spelunking PyPI or site-packages.
- **Maintainers** refresh snapshots when matrix pins or **`[project.dependencies]`** replayt bounds change, with an obvious audit trail (version + date in-tree).
- **Contributors / agents** use the folder as offline context. **`tests/test_reference_documentation.py`** asserts index links, stamp format, and the primary symbol names per **§2–§4** (contract guard, not a substitute for reading upstream docstrings).

## 2. Location and shape

### 2.1 Directory

All curated artifacts live under:

**`docs/reference-documentation/`**

(relative to the repository root).

### 2.2 Index file (normative)

**`docs/reference-documentation/README.md`** MUST exist when this backlog is considered **implemented**. It MUST:

- State that content is a **consumer-side snapshot**, not authoritative replayt documentation.
- Link to **[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md)** **§4.1** (which replayt versions CI exercises).
- Link to **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)** **§2** (integration seam and suggested touchpoints).
- List every sibling markdown artifact (see **§3**) with a one-line description.

### 2.3 Delivery modes (choose at least one)

The Builder MAY satisfy **§3–§4** using either or both:

| Mode | Obligation |
| ---- | ---------- |
| **A) Static markdown** | Committed `.md` files under **`docs/reference-documentation/`**, maintained by hand or produced by a script and committed. |
| **B) Scripted regeneration** | A script under **`scripts/`** (name is Builder’s choice) that regenerates markdown from an **installed** replayt wheel matching a **pinned** version (CLI argument or environment variable). The script MUST be documented in **`docs/reference-documentation/README.md`** (how to run, required args, output paths). Script MUST exit **non-zero** on failure; stdout/stderr SHOULD be suitable for maintainer logs (no secret dumps). |

**CI:** Running the script in CI is **optional**. If the project adds a doc-regeneration job later, **[CI_SPEC.md](CI_SPEC.md)** SHOULD be updated in the same change. This spec does not require a new CI job by itself.

## 3. Content bounds (what MUST appear)

### 3.1 Primary symbols (minimum)

Curated material MUST cover replayt’s public usage surface for **workflow runs** at least for these names (signatures, short behavioral notes, and pointers back to upstream):

- **`Workflow`**
- **`Runner`**
- **`RunContext`**
- **`run_with_mock`**

These are the **integration backbone** described in **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)** **§2.2**. Summaries MAY quote or paraphrase upstream docstrings **briefly**; full upstream prose MUST NOT be copied at length—prefer short excerpts plus “see replayt on PyPI / your installed version for the full text.”

### 3.2 Explicit non-goals

- **No** obligation to mirror replayt’s full **`__all__`** or every public type.
- **No** obligation to host replayt tutorials, CLI docs, or persistence internals unless this package later documents a direct dependency on them in **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)**.
- **No** claim that the snapshot replaces **replayt**’s own release notes or documentation.

### 3.3 Optional extras

The Builder MAY add concise notes for other symbols (e.g. **`RunResult`**, **`RunFailed`**) when they clarify the four primary symbols or match **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)** **§6** failure handling—still bounded and version-stamped per **§4**.

## 4. Version alignment (compatibility matrix)

### 4.1 Matrix pins (normative source)

**[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md)** **§4.1** defines the replayt versions CI exercises (today: **minimum pin** **0.4.0** and **latest** via reinstall). This reference-documentation backlog MUST stay **aligned** with that policy:

- Every curated artifact (each file, or each clearly separated section if using one file) MUST begin with a short, machine- and human-readable **version stamp** block, e.g.:

  ```markdown
  **Source:** `replayt==0.4.0`  
  **Snapshot date:** YYYY-MM-DD
  ```

  Equivalent YAML frontmatter is acceptable if consistent across files.

### 4.2 Coverage rule

When this backlog is **done**, the tree under **`docs/reference-documentation/`** MUST include version-stamped coverage for:

1. **Minimum matrix replayt** — the **same minimum version** CI pins for replayt (currently **`0.4.0`**), and  
2. **Latest matrix replayt** — material refreshed against **PyPI latest** replayt at snapshot time (exact resolved version in the stamp, e.g. **`replayt==0.4.25`**).

**Layout is Builder’s choice:** separate files (e.g. `replayt-0.4.0.md` and `replayt-0.4.x-latest.md`), or one file with two stamped sections—provided **`README.md`** indexes them and stamps meet **§4.1**.

### 4.3 Drift

When **[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md)** **§4.1** changes minimum or **latest** policy, maintainers MUST refresh or extend snapshots in the same PR that updates the matrix docs (or immediately follow with a docs-only PR called out in **[CHANGELOG.md](../CHANGELOG.md)**).

## 5. Repository links (normative)

These links MUST stay in place after Builder delivery; update them if paths or section anchors move.

| Location | Obligation |
| -------- | ---------- |
| **[README.md](../README.md)** | **Reference documentation** section MUST link to **`docs/reference-documentation/`** (when present) **and** to **this spec** as the contract for what belongs there. |
| **[REPLAYT_ECOSYSTEM_IDEA.md](REPLAYT_ECOSYSTEM_IDEA.md)** | MUST mention **`docs/reference-documentation/`** (and optionally this spec) under **tracking replayt releases** or an adjacent bullet so ecosystem readers see the local snapshot story. |
| **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)** | **§1.1** maps this backlog; **§7.2** may reference the folder as the **optional** detailed replayt API snapshot alongside the reference line. |

## 6. Acceptance criteria summary

| Phase | Criterion |
| ----- | --------- |
| **Spec (phase 2)** | This document exists; **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)** **§1.1** maps the backlog here; **[README.md](../README.md)** and **[REPLAYT_ECOSYSTEM_IDEA.md](REPLAYT_ECOSYSTEM_IDEA.md)** are updated to link **this spec** (README already MAY mention the folder—after Builder, links MUST match **§5**). |
| **Builder (phase 3+)** | **`docs/reference-documentation/README.md`** exists; curated content satisfies **§3** and **§4**; optional **`scripts/`** regenerator satisfies **§2.3** mode B if used; README + ecosystem doc links satisfy **§5**; **`tests/test_reference_documentation.py`** (or equivalent) guards the contract; **[CHANGELOG.md](../CHANGELOG.md)** notes user-visible documentation delivery. |

## 7. Related documents

- [COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md) — replayt versions CI proves.
- [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) — integration seam, reference replayt line (**§7.2–7.3**).
- [TESTING_SPEC.md](TESTING_SPEC.md) — replayt public-surface-only test rules (unchanged by this backlog unless extended later).
- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) — explicit contracts and narrow surfaces.
