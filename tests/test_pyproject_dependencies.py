"""Runtime dependency declarations in pyproject.toml match installed wheels."""

from __future__ import annotations

import importlib.metadata as m
import sys
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYPROJECT = _REPO_ROOT / "pyproject.toml"


def _runtime_dependencies() -> list[str]:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    return list(data["project"]["dependencies"])


def _requirement_by_name() -> dict[str, Requirement]:
    out: dict[str, Requirement] = {}
    for dep in _runtime_dependencies():
        req = Requirement(dep)
        out[req.name] = req
    return out


@pytest.mark.parametrize(
    "package",
    ("replayt", "opentelemetry-api", "opentelemetry-sdk"),
)
def test_installed_version_satisfies_pyproject_runtime_spec(package: str) -> None:
    """Each matrix cell and local dev install must satisfy declared specifiers."""
    by_name = _requirement_by_name()
    assert package in by_name, f"no pyproject.toml dependency entry found for {package!r}"
    installed = Version(m.version(package))
    req = by_name[package]
    assert installed in req.specifier, (
        f"{package} {installed} does not satisfy {str(req)!r} from pyproject.toml"
    )


def test_pyproject_declares_replayt_otel_lower_and_otel_upper_bounds() -> None:
    """Lock documented policy: replayt floor, OpenTelemetry 1.x line with <2 cap."""
    by_name = _requirement_by_name()
    assert by_name["replayt"].specifier.contains(Version("0.4.0"))
    for name in ("opentelemetry-api", "opentelemetry-sdk"):
        spec = by_name[name].specifier
        assert spec.contains(Version("1.20.0"))
        assert spec.contains(Version("1.40.0"))
        assert not spec.contains(Version("2.0.0"))


def test_pyproject_otlp_extra_aligns_with_api_sdk_otel_bounds() -> None:
    """COMPATIBILITY_MATRIX_SPEC §3.4 / §7: [otlp] stays on the same OTel major line as API/SDK."""
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    optional = data["project"].get("optional-dependencies") or {}
    otlp = optional.get("otlp") or []
    assert otlp, "pyproject.toml must declare [project.optional-dependencies].otlp"
    otlp_reqs = [Requirement(line) for line in otlp]
    by_extra = {r.name: r for r in otlp_reqs}
    assert "opentelemetry-exporter-otlp-proto-http" in by_extra
    spec = by_extra["opentelemetry-exporter-otlp-proto-http"].specifier
    assert spec.contains(Version("1.20.0"))
    assert spec.contains(Version("1.40.0"))
    assert not spec.contains(Version("2.0.0"))


def test_pyproject_otlp_grpc_extra_mirrors_otlp_http_specifiers() -> None:
    """COMPATIBILITY_MATRIX_SPEC 3.4.2 / TESTING_SPEC 4.6: [otlp-grpc] matches [otlp] bounds."""
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    optional = data["project"].get("optional-dependencies") or {}
    otlp = optional.get("otlp") or []
    otlp_grpc = optional.get("otlp-grpc") or []
    assert otlp_grpc, "pyproject.toml must declare [project.optional-dependencies].otlp-grpc"
    http_by_name = {Requirement(line).name: Requirement(line) for line in otlp}
    grpc_by_name = {Requirement(line).name: Requirement(line) for line in otlp_grpc}
    assert "opentelemetry-exporter-otlp-proto-http" in http_by_name
    assert "opentelemetry-exporter-otlp-proto-grpc" in grpc_by_name
    http_spec = http_by_name["opentelemetry-exporter-otlp-proto-http"].specifier
    grpc_spec = grpc_by_name["opentelemetry-exporter-otlp-proto-grpc"].specifier
    assert str(http_spec) == str(grpc_spec), (
        f"[otlp] HTTP specifier {http_spec!r} must match [otlp-grpc] gRPC specifier {grpc_spec!r}"
    )


def test_requires_python_matches_project_and_runtime() -> None:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    assert data["project"]["requires-python"] == ">=3.11"
    assert sys.version_info[:2] >= (3, 11)
