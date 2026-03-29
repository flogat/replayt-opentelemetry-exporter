#!/usr/bin/env python3
"""Find latest opentelemetry-api / opentelemetry-sdk pair with major >= 2 on PyPI.

Used by `.github/workflows/otel-2x-spike.yml`. When no 2.x pair exists, exits 0
with empty output (spike skipped per COMPATIBILITY_MATRIX_SPEC §7.2 step 0).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from packaging.version import InvalidVersion, Version

_PYPI_JSON = "https://pypi.org/pypi/{package}/json"


def _fetch_releases(package: str, *, timeout_s: float = 30.0) -> dict[str, Any]:
    url = _PYPI_JSON.format(package=package)
    req = urllib.request.Request(url, headers={"User-Agent": "replayt-otel-2x-spike-probe"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.load(resp)


def release_keys(payload: dict[str, Any]) -> frozenset[str]:
    rel = payload.get("releases")
    if not isinstance(rel, dict):
        return frozenset()
    return frozenset(rel.keys())


def best_version_key(keys: frozenset[str], *, min_major: int) -> str | None:
    """Return the highest version string whose major is >= min_major."""
    best: tuple[Version, str] | None = None
    for key in keys:
        try:
            parsed = Version(key)
        except InvalidVersion:
            continue
        if parsed.major < min_major:
            continue
        if best is None or parsed > best[0]:
            best = (parsed, key)
    return best[1] if best else None


def latest_paired_otel_2x(
    *,
    min_major: int = 2,
    timeout_s: float = 30.0,
    api_payload: dict[str, Any] | None = None,
    sdk_payload: dict[str, Any] | None = None,
) -> str | None:
    """Return a version string present in both API and SDK PyPI releases, or None."""
    if api_payload is not None:
        api_data = api_payload
    else:
        api_data = _fetch_releases("opentelemetry-api", timeout_s=timeout_s)
    if sdk_payload is not None:
        sdk_data = sdk_payload
    else:
        sdk_data = _fetch_releases("opentelemetry-sdk", timeout_s=timeout_s)
    api_keys = release_keys(api_data)
    sdk_keys = release_keys(sdk_data)
    candidates = api_keys & sdk_keys
    return best_version_key(candidates, min_major=min_major)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="Append version=... to GITHUB_OUTPUT when running in GitHub Actions",
    )
    args = parser.parse_args(argv)

    try:
        version = latest_paired_otel_2x()
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError) as e:
        print(f"otel_2x_probe: PyPI request failed: {e}", file=sys.stderr)
        return 1

    if args.github_output:
        out_path = os.environ.get("GITHUB_OUTPUT")
        if out_path:
            with open(out_path, "a", encoding="utf-8") as fh:
                fh.write(f"version={version or ''}\n")
        else:
            print("otel_2x_probe: --github-output set but GITHUB_OUTPUT unset", file=sys.stderr)
            return 1
    else:
        print(version or "")

    if version:
        print(f"otel_2x_probe: selected paired OpenTelemetry {version} for spike", file=sys.stderr)
    else:
        print(
            "otel_2x_probe: no paired opentelemetry-api / opentelemetry-sdk "
            "2.x on PyPI; spike skipped",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
