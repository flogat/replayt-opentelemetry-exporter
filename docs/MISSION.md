# Mission: OpenTelemetry traces and metrics for replayt workflow runs

This package adds **OpenTelemetry traces and metrics** around **replayt** workflow runs so operators and integrators can
observe runs in their existing backends (Jaeger, Prometheus-compatible collectors, vendor APM, and so on) without
changing replayt core.

For **how we integrate** (versioning, narrow APIs, consumer-side maintenance, and not using this repo to steer replayt
core), see **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)**. For **ecosystem positioning** and pattern choice, see
**[REPLAYT_ECOSYSTEM_IDEA.md](REPLAYT_ECOSYSTEM_IDEA.md)**—this project is best read as a **core-gap** satellite:
replayt does not ship first-party OpenTelemetry instrumentation; this repository provides that capability as an
optional adapter.

## Users / problem

| Audience | Problem this removes |
| -------- | -------------------- |
| **Maintainers** | No shared story for what the exporter guarantees, what replayt versions are in scope, or how to ship changes without surprising integrators. |
| **Integrators** | They need stable hooks and documented compatibility so they can wire replayt runs into company-standard observability without forking replayt. |
| **Operators** | They need traces and metrics that explain latency, failures, and throughput of workflow runs in production tooling they already run. |
| **Contributors** | They need a single place for scope, success expectations, and where consumer-side work stops so reviews stay focused on this adapter—not replayt core. |

Without this mission, review and prioritization drift toward “change replayt” or unclear ownership; this document keeps
expectations on the **consumer-side** model described in the design principles.

## Replayt’s role

- **What we rely on:** Public replayt APIs and workflow/run lifecycle hooks that this package instruments or wraps.
  Exact touchpoints evolve with replayt releases and are documented alongside version support in the README or a
  compatibility note as the implementation grows.
- **What stays consumer-side:** Pins, shims, adapter code, and tests for those boundaries live **in this repository**.
  We track replayt releases here (changelog, optional matrix in CI) and fix breakages by updating this package—not by
  treating this repo as a lever to redirect replayt core roadmaps.
- **Upstream proposals:** Improvements that belong in replayt itself go through replayt’s normal contribution channels;
  this repo does not substitute for that process (see design principle **Not a lever on core**).

## Scope

**In scope (this package owns)**

- Emitting OpenTelemetry **traces and/or metrics** for replayt workflow runs using documented, minimal public surfaces, including **lifecycle-oriented** traces (start, milestones where recorded, completion) with **human-readable, low-cardinality** status and attributes as specified in **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)** **§6**.
- Documenting supported replayt and OpenTelemetry versions, and how to configure export (endpoints, resource attrs, and
  similar knobs as the API stabilizes).
- **Consumer-side** compatibility: dependency pins, migration notes, and tests at the integration boundary with replayt.

**Out of scope / delegated**

- **Replayt core** behavior, release cadence, and feature decisions.
- Choosing or operating a specific vendor backend (we document export; operators own collectors and retention).
- A guarantee of feature parity with every possible replayt deployment mode until explicitly documented and tested.

## Success

Concrete outcomes we optimize for:

1. **CI green** — Every pull request keeps the pipeline **green**: **Ruff** (lint + format check) and **pytest** for
   behavior we claim. Tests cover unit logic and, where valuable, contract-style checks against replayt’s public
   surface (see `.github/workflows/ci.yml` for the exact commands).
2. **How to run tests locally** — After a dev install (`pip install -e ".[dev]"` from the repository root), run:

   ```bash
   pytest
   ```

   Match CI with `ruff check .` and `ruff format --check .` from the repo root (or `python -m ruff …` if you prefer
   invoking Ruff as a module).
3. **Documented runbook** — The README describes how to enable the exporter and verify spans (and, when shipped,
   metrics) in a dev environment—operators and integrators should not need to read source to get a first successful
   export.
4. **Aligned docs** — Mission, **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)**,
   **[REPLAYT_ECOSYSTEM_IDEA.md](REPLAYT_ECOSYSTEM_IDEA.md)**,
   **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md)**,
   **[COMPATIBILITY_MATRIX_SPEC.md](COMPATIBILITY_MATRIX_SPEC.md)**, and
   **[TESTING_SPEC.md](TESTING_SPEC.md)** stay consistent on consumer-side maintenance, ecosystem role, the
   documented public surface, version/matrix policy, and **what tests must prove** (this package stays compatible by pins, tests, and notes **here**; it does not steer
   replayt core—see **Not a lever on core** in the design principles).

Meeting these criteria means integrators can adopt the package with clear expectations, and maintainers can review
changes without scope creep into replayt core.
