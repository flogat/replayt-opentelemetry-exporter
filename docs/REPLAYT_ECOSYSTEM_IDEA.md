# Positioning — OpenTelemetry traces and metrics for replayt workflow runs

This project **uses** [replayt](https://pypi.org/project/replayt/). It is **not** a fork of replayt. Compatibility,
version pins, and CI are **your** responsibility here.

**Test coverage (required):** ship automated tests for behavior you claim (unit, contract/integration at replayt
boundaries, smoke where useful). Document how to run them in the README and CI.

Pick **one primary** pattern below (you may blend—say which leads):

## 1) Core-gap

_Use when replayt core intentionally omits a capability._

- What is out of core and why?
- What does **this** repo provide instead?
- How do you track replayt releases?

## 2) LLM showcase

_Concrete demo that needs model calls._

- One-sentence use case; which replayt primitives you exercise
- LLM boundaries: secrets, cost, redaction
- What a reviewer runs to verify

## 3) Framework bridge

_Adapter to another framework or runtime._

- Target framework; public API of the bridge
- How **you** maintain consumer-side compatibility (pins, CI matrix)

## 4) Combinator

_Novel composition of replayt + other tools._

- What is stronger together; shared conventions; integration tests where feasible

## Your choice

- **Primary pattern:** **1) Core-gap** — replayt does not ship first-party OpenTelemetry instrumentation; this repository
  provides traces and metrics for workflow runs as an optional consumer-side adapter.
- **One-paragraph pitch:** Integrators plug this package into replayt-powered apps to export **workflow run traces** to
  standard OpenTelemetry pipelines (metrics can follow as public lifecycle APIs stabilize), while keeping compatibility
  pins, tests, and release notes in this repo—not in replayt core.
