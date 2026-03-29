"""docs/reference-documentation/ meets REFERENCE_DOCUMENTATION_SPEC.md §2–§4 (Builder guard)."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REF_DIR = _REPO_ROOT / "docs" / "reference-documentation"
_INDEX = _REF_DIR / "README.md"
_SNAPSHOT_MIN = _REF_DIR / "replayt-0.4.0.md"
_SNAPSHOT_LATEST = _REF_DIR / "replayt-latest.md"
_REQUIRED_SYMBOLS = ("Workflow", "Runner", "RunContext", "run_with_mock")
_STAMP_SOURCE = re.compile(r"\*\*Source:\*\*\s*`replayt==[\d.]+`", re.MULTILINE)
_STAMP_DATE = re.compile(r"\*\*Snapshot date:\*\*\s*\d{4}-\d{2}-\d{2}")


def test_reference_documentation_index_exists() -> None:
    assert _INDEX.is_file(), f"missing {_INDEX}"


def test_reference_documentation_index_contract() -> None:
    """README links matrix §4.1, PUBLIC_API §2, and lists snapshot siblings."""
    text = _INDEX.read_text(encoding="utf-8")

    assert "consumer-side" in text.lower() or "Consumer-side" in text
    assert "COMPATIBILITY_MATRIX_SPEC.md" in text
    assert "§4.1" in text
    assert "PUBLIC_API_SPEC.md" in text
    assert "§2" in text
    assert "REFERENCE_DOCUMENTATION_SPEC.md" in text

    for name in ("replayt-0.4.0.md", "replayt-latest.md"):
        assert name in text, f"index must list {name}"


def test_reference_documentation_snapshots() -> None:
    for path in (_SNAPSHOT_MIN, _SNAPSHOT_LATEST):
        assert path.is_file(), f"missing {path}"
        body = path.read_text(encoding="utf-8")
        assert _STAMP_SOURCE.search(body), f"{path.name} missing **Source:** `replayt==…` stamp"
        assert _STAMP_DATE.search(body), f"{path.name} missing **Snapshot date:** YYYY-MM-DD stamp"
        for sym in _REQUIRED_SYMBOLS:
            assert sym in body, f"{path.name} must mention {sym}"

    assert "replayt==0.4.0" in _SNAPSHOT_MIN.read_text(encoding="utf-8")
    latest = _SNAPSHOT_LATEST.read_text(encoding="utf-8")
    assert "redact_keys" in latest or "policy_hooks" in latest
