"""RELEASE_ENGINEERING_SPEC §6.4 — distribution version matches pyproject and __version__."""

from __future__ import annotations

import importlib.metadata as m
import tomllib
from pathlib import Path

import replayt_opentelemetry_exporter as pkg

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_DIST_NAME = "replayt-opentelemetry-exporter"


def test_package_version_matches_pyproject_and_importlib_metadata() -> None:
    """Strategy B: one literal in pyproject; runtime and metadata stay aligned."""
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    declared = data["project"]["version"]
    installed = m.version(_DIST_NAME)
    assert pkg.__version__ == declared, (
        f"replayt_opentelemetry_exporter.__version__ {pkg.__version__!r} != "
        f"pyproject [project].version {declared!r}"
    )
    assert installed == declared, (
        f"importlib.metadata.version({_DIST_NAME!r}) {installed!r} != "
        f"pyproject [project].version {declared!r}"
    )
