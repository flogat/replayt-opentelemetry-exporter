"""GitHub Actions workflow matches docs/CI_SPEC.md for jobs test and test-python-3-11."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI_YML = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci() -> dict:
    assert _CI_YML.is_file(), f"missing {_CI_YML}"
    return yaml.safe_load(_CI_YML.read_text(encoding="utf-8"))


def _job_steps(data: dict, job_id: str) -> list[dict]:
    jobs = data.get("jobs") or {}
    job = jobs.get(job_id)
    assert job is not None, f"ci.yml must define job {job_id!r}"
    steps = job.get("steps")
    assert isinstance(steps, list) and steps, f"job {job_id!r} must have non-empty steps"
    return steps


def _test_job_steps(data: dict) -> list[dict]:
    return _job_steps(data, "test")


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


def test_ci_permissions_minimal_contents_read() -> None:
    """CI_SPEC §3.3 — default minimal read for contents."""
    data = _load_ci()
    perms = data.get("permissions")
    assert perms == {"contents": "read"}, (
        f"top-level permissions should be contents: read only, got {perms!r}"
    )


def test_ci_test_job_ruff_pytest_steps_and_commands() -> None:
    """CI_SPEC §3.1–§3.2 — separate steps with expected commands; exits not masked."""
    data = _load_ci()
    pairs = _named_run_steps(_test_job_steps(data))
    by_name = {n: r for n, r in pairs}

    assert "Ruff check" in by_name
    assert by_name["Ruff check"] == "ruff check src tests"

    assert "Ruff format" in by_name
    assert by_name["Ruff format"] == "ruff format --check src tests"

    assert "Run tests" in by_name
    assert by_name["Run tests"] == "pytest -q"

    ruff_check_idx = next(i for i, (n, _) in enumerate(pairs) if n == "Ruff check")
    ruff_fmt_idx = next(i for i, (n, _) in enumerate(pairs) if n == "Ruff format")
    pytest_idx = next(i for i, (n, _) in enumerate(pairs) if n == "Run tests")
    assert ruff_check_idx < ruff_fmt_idx < pytest_idx, (
        "Ruff check, Ruff format, then Run tests must stay ordered for failure surfacing"
    )

    for label, cmd in (
        ("Ruff check", by_name["Ruff check"]),
        ("Ruff format", by_name["Ruff format"]),
        ("Run tests", by_name["Run tests"]),
    ):
        assert "|| true" not in cmd, f"{label} must not mask non-zero exit with || true"


def test_ci_test_job_logs_dependency_versions_before_checks() -> None:
    """CI_SPEC §3.1 item 2 — audit log before Ruff/pytest in the same job."""
    data = _load_ci()
    pairs = _named_run_steps(_test_job_steps(data))
    names = [n for n, _ in pairs]
    audit = "Print resolved dependency versions (matrix audit)"
    assert audit in names, f"expected step {audit!r}"
    assert "Ruff check" in names
    assert names.index(audit) < names.index("Ruff check")


def test_ci_has_schedule_for_supplemental_python_311() -> None:
    """CI_SPEC §3.6 — supplemental 3.11 reachable via schedule and workflow_dispatch."""
    data = _load_ci()
    on = data.get("on")
    assert isinstance(on, dict), "ci.yml top-level on: must be a mapping"
    sched = on.get("schedule")
    assert isinstance(sched, list) and sched, "on.schedule must be a non-empty list"
    assert any(isinstance(item, dict) and "cron" in item for item in sched), (
        "on.schedule must include at least one cron mapping"
    )
    assert "workflow_dispatch" in on, "on.workflow_dispatch must be present"


def test_ci_supplemental_python_311_job_ruff_pytest_and_audit() -> None:
    """CI_SPEC §3.6 / COMPATIBILITY §4.3 — same Ruff/pytest as test; audit before checks."""
    data = _load_ci()
    job = (data.get("jobs") or {}).get("test-python-3-11")
    assert job is not None, "ci.yml must define job 'test-python-3-11'"
    assert job.get("if") == (
        "github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'"
    )

    steps = _job_steps(data, "test-python-3-11")
    setup_py = None
    for step in steps:
        if isinstance(step, dict) and step.get("uses") == "actions/setup-python@v5":
            setup_py = step.get("with") or {}
            break
    assert setup_py is not None, "test-python-3-11 must use actions/setup-python@v5"
    assert setup_py.get("python-version") == "3.11"

    pairs = _named_run_steps(steps)
    by_name = {n: r for n, r in pairs}
    assert "Apply pins (replayt latest + OpenTelemetry API/SDK 1.40.0)" in by_name
    pins = by_name["Apply pins (replayt latest + OpenTelemetry API/SDK 1.40.0)"]
    assert "opentelemetry-api==1.40.0" in pins
    assert "opentelemetry-sdk==1.40.0" in pins
    assert "replayt" in pins.lower()

    assert by_name.get("Ruff check") == "ruff check src tests"
    assert by_name.get("Ruff format") == "ruff format --check src tests"
    assert by_name.get("Run tests") == "pytest -q"

    names = [n for n, _ in pairs]
    audit = "Print resolved dependency versions (matrix audit)"
    assert audit in names
    assert names.index(audit) < names.index("Ruff check")

    for label, cmd in (
        ("Ruff check", by_name["Ruff check"]),
        ("Ruff format", by_name["Ruff format"]),
        ("Run tests", by_name["Run tests"]),
    ):
        assert "|| true" not in cmd, f"{label} must not mask non-zero exit with || true"
