"""Optional PyPI index check for [docs/PUBLIC_API_SPEC.md](docs/PUBLIC_API_SPEC.md) §8 item 17.

Default CI does not call the network. After the first successful upload, maintainers can run:

    VERIFY_PYPI_INDEX=1 pytest tests/test_pypi_index.py -q
"""

from __future__ import annotations

import json
import os
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_DIST_NAME = "replayt-opentelemetry-exporter"
_PYPI_JSON_URL = f"https://pypi.org/pypi/{_DIST_NAME}/json"


def _declared_version() -> str:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["version"]


def _pypi_verify_enabled() -> bool:
    return os.environ.get("VERIFY_PYPI_INDEX", "").strip().lower() in ("1", "true", "yes")


@pytest.mark.skipif(
    not _pypi_verify_enabled(),
    reason="Set VERIFY_PYPI_INDEX=1 to check PyPI lists [project].version.",
)
def test_pypi_lists_version_matching_pyproject() -> None:
    declared = _declared_version()
    ua = (
        "replayt-opentelemetry-exporter-tests "
        "(pytest; +https://pypi.org/pypi/replayt-opentelemetry-exporter/)"
    )
    req = urllib.request.Request(_PYPI_JSON_URL, headers={"User-Agent": ua}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            pytest.fail(
                f"PyPI has no project {_DIST_NAME!r} yet, or the name is wrong. "
                "Publish per README Releases and PyPI and docs/RELEASE_ENGINEERING_SPEC.md §4."
            )
        raise
    payload = json.loads(raw.decode("utf-8"))
    info = payload.get("info") or {}
    assert info.get("name", "").lower().replace("_", "-") == _DIST_NAME, (
        f"PyPI JSON name {info.get('name')!r} does not match distribution {_DIST_NAME!r}"
    )
    published = info.get("version")
    assert published == declared, (
        f"PyPI latest version {published!r} != pyproject [project].version {declared!r}. "
        "Cut a release or fix the index before closing §8 item 17."
    )
