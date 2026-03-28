"""GitHub Actions workflow matches docs/CI_SPEC.md obligations for job test."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI_YML = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci() -> dict:
    assert _CI_YML.is_file(), f"missing {_CI_YML}"
    return yaml.safe_load(_CI_YML.read_text(encoding="utf-8"))


def _test_job_steps(data: dict) -> list[dict]:
    jobs = data.get("jobs") or {}
    test = jobs.get("test")
    assert test is not None, "ci.yml must define job 'test'"
    steps = test.get("steps")
    assert isinstance(steps, list) and steps, "job 'test' must have non-empty steps"
    return steps


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
