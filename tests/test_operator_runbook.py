"""docs/OPERATOR_RUNBOOK.md meets docs/OPERATOR_MONITORING_SPEC.md §4–§7 obligations."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RUNBOOK = _REPO_ROOT / "docs" / "OPERATOR_RUNBOOK.md"


def test_operator_runbook_exists() -> None:
    assert _RUNBOOK.is_file(), f"missing {_RUNBOOK}"


def test_operator_runbook_contract() -> None:
    """OPERATOR_MONITORING_SPEC §2, §4–§7 (scrape caveat, PromQL, panels, alerts, non-goals)."""
    text = _RUNBOOK.read_text(encoding="utf-8")

    assert "PUBLIC_API_SPEC.md" in text
    assert "§5" in text and "§6" in text

    # §2 — verify names on scrape / OTLP → Prometheus caveat
    assert re.search(r"scrape|/metrics|metrics explorer", text, re.I)

    # §4.1 outcomes — counter + rate + failure ratio
    assert "replayt_workflow_run_outcomes_total" in text
    assert "rate(" in text and "workflow_id" in text and "outcome" in text
    assert "failure" in text.lower()

    # §4.2 duration — histogram buckets + p95 + non-Prometheus path
    assert "replayt_workflow_run_duration_ms_bucket" in text
    assert "histogram_quantile" in text
    assert re.search(r"p95|0\.95", text)

    # §4.3 exporter errors — normalized error_type set + rate example
    for et in ("export_failed", "serialization_error", "timeout", "unknown"):
        assert et in text
    assert "replayt_exporter_errors_total" in text

    # §5 — Grafana / panel intents (at least three concepts; we ship four rows)
    assert "Grafana" in text
    assert "Run rate" in text or "outcomes" in text
    assert "Failure ratio" in text or "failure ratio" in text.lower()
    assert re.search(r"Latency|p95|heatmap", text, re.I)
    assert "Exporter errors" in text or "exporter errors" in text.lower()

    # §6 — three alert starting points: failure ratio 15m, exporter errors, latency
    assert "15m" in text
    assert "increase(" in text and "replayt_exporter_errors_total" in text
    assert re.search(r"10m|5m", text)
    assert re.search(r"latency|p95", text, re.I)

    # §6 optional trace drill-down
    assert "replayt.workflow.run" in text

    # §7 — no need to read tracing.py for basic wiring
    assert "tracing.py" in text
