"""GitHub Actions workflow matches docs/CI_SPEC.md for job test."""

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


def test_ci_test_job_matrix_requires_python_parity() -> None:
    """CI_SPEC §3.6 / COMPATIBILITY_MATRIX_SPEC §4.1 — eight merge-blocking rows."""
    data = _load_ci()
    job = (data.get("jobs") or {}).get("test")
    assert job is not None
    strategy = job.get("strategy") or {}
    matrix = strategy.get("matrix") or {}
    include = matrix.get("include")
    if not isinstance(include, list) or len(include) != 8:
        got = len(include) if isinstance(include, list) else repr(include)
        raise AssertionError(f"test job matrix.include must have 8 rows, got {got}")

    base_cells = [
        ("0.4.0", "1.20.0"),
        ("0.4.0", "1.40.0"),
        ("latest", "1.20.0"),
        ("latest", "1.40.0"),
    ]
    py_counts: dict[str, int] = {}
    seen_pairs: dict[tuple[str, str, str], int] = {}
    for row in include:
        assert isinstance(row, dict), f"matrix row must be a mapping, got {row!r}"
        py = row.get("python-version")
        rt = row.get("replayt")
        ot = row.get("otel")
        assert py in ("3.11", "3.12"), f"unexpected python-version {py!r} in {row!r}"
        assert (rt, ot) in base_cells, f"unexpected replayt/otel in {row!r}"
        py_counts[py] = py_counts.get(py, 0) + 1
        key = (str(py), str(rt), str(ot))
        seen_pairs[key] = seen_pairs.get(key, 0) + 1

    assert py_counts == {"3.11": 4, "3.12": 4}, (
        f"expected four rows per Python minor, got {py_counts!r}"
    )
    for cell in base_cells:
        assert seen_pairs.get(("3.11", cell[0], cell[1])) == 1, f"missing 3.11 row for {cell}"
        assert seen_pairs.get(("3.12", cell[0], cell[1])) == 1, f"missing 3.12 row for {cell}"


def test_ci_test_job_setup_python_uses_matrix_version() -> None:
    """Each test matrix row must install the matrix Python minor."""
    data = _load_ci()
    steps = _test_job_steps(data)
    setup = None
    for step in steps:
        if isinstance(step, dict) and step.get("uses") == "actions/setup-python@v5":
            setup = step.get("with") or {}
            break
    assert setup is not None, "test job must use actions/setup-python@v5"
    assert setup.get("python-version") == "${{ matrix.python-version }}", (
        f"setup-python python-version must follow matrix, got {setup.get('python-version')!r}"
    )


def test_ci_no_supplemental_python_311_job_or_schedule_only_cron() -> None:
    """COMPATIBILITY_MATRIX_SPEC §4.3 — transitional job removed when §4.1 is satisfied."""
    data = _load_ci()
    jobs = data.get("jobs") or {}
    assert "test-python-3-11" not in jobs, "test-python-3-11 must be removed after parity"
    on = data.get("on")
    assert isinstance(on, dict), "ci.yml top-level on: must be a mapping"
    assert "schedule" not in on, "on.schedule must be absent once supplemental 3.11 job is removed"
    assert "workflow_dispatch" in on, "on.workflow_dispatch must remain available"


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
