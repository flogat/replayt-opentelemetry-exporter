"""Non-blocking OpenTelemetry 2.x spike workflow (CI_SPEC 2.4, COMPATIBILITY_MATRIX_SPEC 7.5)."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SPIKE_YML = _REPO_ROOT / ".github" / "workflows" / "otel-2x-spike.yml"


def _load_spike() -> dict:
    assert _SPIKE_YML.is_file(), f"missing {_SPIKE_YML}"
    return yaml.safe_load(_SPIKE_YML.read_text(encoding="utf-8"))


def _named_run_steps(steps: list[dict]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        name = step.get("name")
        run = step.get("run")
        if isinstance(name, str) and isinstance(run, str):
            out.append((name, run.strip()))
    return out


def test_otel_2x_spike_permissions_minimal_contents_read() -> None:
    data = _load_spike()
    assert data.get("permissions") == {"contents": "read"}


def test_otel_2x_spike_triggers_non_blocking() -> None:
    data = _load_spike()
    on = data.get("on")
    assert isinstance(on, dict)
    assert "workflow_dispatch" in on
    assert "schedule" in on


def test_otel_2x_spike_job_id_and_ruff_pytest_order() -> None:
    data = _load_spike()
    jobs = data.get("jobs") or {}
    assert "otel-2x-spike" in jobs
    steps = jobs["otel-2x-spike"].get("steps") or []
    pairs = _named_run_steps(steps)
    by_name = {n: r for n, r in pairs}

    assert "Ruff check" in by_name
    assert by_name["Ruff check"] == "ruff check src tests"
    assert "Ruff format" in by_name
    assert by_name["Ruff format"] == "ruff format --check src tests"
    assert "Run tests" in by_name
    assert by_name["Run tests"] == "pytest -q"

    names = [n for n, _ in pairs]
    audit = "Print resolved dependency versions (spike audit)"
    assert audit in names
    assert names.index(audit) < names.index("Ruff check")
    ruff_idx = names.index("Ruff check")
    fmt_idx = names.index("Ruff format")
    pytest_idx = names.index("Run tests")
    assert ruff_idx < fmt_idx < pytest_idx

    for label, cmd in (
        ("Ruff check", by_name["Ruff check"]),
        ("Ruff format", by_name["Ruff format"]),
        ("Run tests", by_name["Run tests"]),
    ):
        assert "|| true" not in cmd, f"{label} must not mask non-zero exit with || true"


def test_otel_2x_spike_uses_probe_script() -> None:
    data = _load_spike()
    steps = (data.get("jobs") or {}).get("otel-2x-spike", {}).get("steps") or []
    probe_runs = [s.get("run", "") for s in steps if isinstance(s, dict) and s.get("id") == "probe"]
    assert probe_runs, "expected step with id: probe"
    assert any("scripts/otel_2x_probe.py" in r for r in probe_runs)
