# Reference documentation (replayt workflow / run surface)

This directory holds **consumer-side snapshots** of a small part of [replayt](https://pypi.org/project/replayt/)’s public API. It is **not** authoritative replayt documentation. For full docstrings and release notes, use the PyPI page and the wheel you install.

**Normative contract:** [REFERENCE_DOCUMENTATION_SPEC.md](../REFERENCE_DOCUMENTATION_SPEC.md).

**Which replayt versions matter here:** [COMPATIBILITY_MATRIX_SPEC.md](../COMPATIBILITY_MATRIX_SPEC.md) **§4.1** — CI runs **pytest** with replayt pinned to **0.4.0** and to **latest** (upgrade reinstall), crossed with OpenTelemetry API/SDK pins.

**How this package uses replayt:** [PUBLIC_API_SPEC.md](../PUBLIC_API_SPEC.md) **§2** (integration seam and suggested touchpoints).

## Files

| File | Description |
| ---- | ----------- |
| [replayt-0.4.0.md](replayt-0.4.0.md) | **Workflow**, **Runner**, **RunContext**, **run_with_mock** — signatures and short notes for **`replayt==0.4.0`** (matrix minimum). |
| [replayt-latest.md](replayt-latest.md) | Same symbols for **PyPI latest** at snapshot time (resolved version in the stamp). |

When [COMPATIBILITY_MATRIX_SPEC.md](../COMPATIBILITY_MATRIX_SPEC.md) **§4.1** or this repo’s replayt lower bound changes, refresh these files in the same change set (or a follow-up docs PR) per [REFERENCE_DOCUMENTATION_SPEC.md](../REFERENCE_DOCUMENTATION_SPEC.md) **§4.3**.
