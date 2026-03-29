"""Publish workflow matches RELEASE_ENGINEERING_SPEC §5.2 intent (tag-gated, OIDC)."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PUBLISH_YML = _REPO_ROOT / ".github" / "workflows" / "publish-pypi.yml"


def _load_publish() -> dict:
    assert _PUBLISH_YML.is_file(), f"missing {_PUBLISH_YML}"
    return yaml.safe_load(_PUBLISH_YML.read_text(encoding="utf-8"))


def test_publish_workflow_permissions_oidc_and_tag_trigger() -> None:
    data = _load_publish()
    assert data.get("permissions") == {"contents": "read", "id-token": "write"}, (
        f"expected contents: read and id-token: write, got {data.get('permissions')!r}"
    )
    on = data.get("on") or {}
    push = on.get("push") or {}
    tags = push.get("tags")
    assert isinstance(tags, list) and tags, "on.push.tags must be a non-empty list"
    jobs = data.get("jobs") or {}
    publish = jobs.get("publish")
    assert publish is not None, "publish-pypi.yml must define job 'publish'"
    steps = publish.get("steps")
    assert isinstance(steps, list) and steps, "job 'publish' must have non-empty steps"
    uses_lines = [s.get("uses") for s in steps if isinstance(s, dict) and s.get("uses")]
    assert any(
        isinstance(u, str) and u.startswith("pypa/gh-action-pypi-publish@") for u in uses_lines
    ), "expected pypa/gh-action-pypi-publish step"
    run_blocks = [s.get("run") for s in steps if isinstance(s, dict) and s.get("run")]
    joined = "\n".join(r for r in run_blocks if isinstance(r, str))
    assert "python -m build" in joined, "expected python -m build in a run step"
    assert "twine check" in joined, "expected twine check dist/* in a run step"
