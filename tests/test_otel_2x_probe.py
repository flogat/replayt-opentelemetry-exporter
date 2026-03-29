"""Unit tests for scripts/otel_2x_probe.py (OpenTelemetry 2.x PyPI pairing)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROBE_PATH = _REPO_ROOT / "scripts" / "otel_2x_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("otel_2x_probe", _PROBE_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


probe = _load_probe()


def test_release_keys_empty_or_invalid_payload() -> None:
    assert probe.release_keys({}) == frozenset()
    assert probe.release_keys({"releases": None}) == frozenset()
    assert probe.release_keys({"releases": []}) == frozenset()


def test_best_version_key_picks_highest_major2() -> None:
    keys = frozenset({"1.40.0", "2.0.0", "2.1.0"})
    assert probe.best_version_key(keys, min_major=2) == "2.1.0"


def test_best_version_key_prefers_stable_over_prerelease() -> None:
    keys = frozenset({"2.0.0b1", "2.0.0"})
    assert probe.best_version_key(keys, min_major=2) == "2.0.0"


def test_best_version_key_none_when_below_major() -> None:
    keys = frozenset({"1.40.0", "1.99.0"})
    assert probe.best_version_key(keys, min_major=2) is None


def test_best_version_key_ignores_invalid_tokens() -> None:
    keys = frozenset({"not-a-version", "2.0.0"})
    assert probe.best_version_key(keys, min_major=2) == "2.0.0"


def test_latest_paired_otel_2x_requires_intersection() -> None:
    api = {"releases": {"2.0.0": []}}
    sdk = {"releases": {"1.40.0": []}}
    assert probe.latest_paired_otel_2x(api_payload=api, sdk_payload=sdk) is None


def test_latest_paired_otel_2x_returns_highest_shared() -> None:
    api = {"releases": {"1.40.0": [], "2.0.0": [], "2.1.0": []}}
    sdk = {"releases": {"1.40.0": [], "2.0.0": [], "2.1.0": []}}
    assert probe.latest_paired_otel_2x(api_payload=api, sdk_payload=sdk) == "2.1.0"


def test_main_github_output_writes_version(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    out_file = tmp_path / "gh_out"
    out_file.write_text("", encoding="utf-8")
    api = {"releases": {"2.0.0": []}}
    sdk = {"releases": {"2.0.0": []}}
    real_latest = probe.latest_paired_otel_2x

    monkeypatch.setattr(
        probe,
        "latest_paired_otel_2x",
        lambda **kw: real_latest(api_payload=api, sdk_payload=sdk),
    )

    old = os.environ.get("GITHUB_OUTPUT")
    try:
        os.environ["GITHUB_OUTPUT"] = str(out_file)
        rc = probe.main(["--github-output"])
    finally:
        if old is None:
            os.environ.pop("GITHUB_OUTPUT", None)
        else:
            os.environ["GITHUB_OUTPUT"] = old

    assert rc == 0
    written = out_file.read_text(encoding="utf-8")
    assert "version=2.0.0" in written


def test_main_github_output_empty_when_no_pair(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    out_file = tmp_path / "gh_out"
    api = {"releases": {"1.40.0": []}}
    sdk = {"releases": {"1.40.0": []}}
    real_latest = probe.latest_paired_otel_2x

    monkeypatch.setattr(
        probe,
        "latest_paired_otel_2x",
        lambda **kw: real_latest(api_payload=api, sdk_payload=sdk),
    )

    old = os.environ.get("GITHUB_OUTPUT")
    try:
        os.environ["GITHUB_OUTPUT"] = str(out_file)
        rc = probe.main(["--github-output"])
    finally:
        if old is None:
            os.environ.pop("GITHUB_OUTPUT", None)
        else:
            os.environ["GITHUB_OUTPUT"] = old

    assert rc == 0
    assert "version=\n" in out_file.read_text(encoding="utf-8")


def test_main_github_output_requires_env_var() -> None:
    old = os.environ.pop("GITHUB_OUTPUT", None)
    try:
        rc = probe.main(["--github-output"])
    finally:
        if old is not None:
            os.environ["GITHUB_OUTPUT"] = old
    assert rc == 1
