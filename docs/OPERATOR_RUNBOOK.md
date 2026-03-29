# Operator runbook: canonical replayt exporter metrics

This runbook maps the three canonical metrics from [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5** to **Prometheus-style** queries, **Grafana-style** panel ideas, and **alert starting points**. Label semantics, cardinality, and trace drill-down keys are normative in **§5.2–§5.4** and **§6** of that document; **§5.7** and **§6.8** describe how those metric and trace names relate to OpenTelemetry semantic conventions and what happens when names change.

## Verify names and labels on your scrape

OpenTelemetry instruments use **dotted** names (for example `replayt.workflow.run.outcomes_total`). After OTLP export and conversion to Prometheus (or a compatible scrape format), series names often use **underscores** (for example `replayt_workflow_run_outcomes_total`). Attribute keys usually become **label** names with the same spelling.

**Before copying queries into dashboards or alerts**, open your scrape target, metrics explorer, or `/metrics` output and confirm the exact **metric names** and **label keys**. Vendors may rename buckets, units, or prefixes. Examples below assume the underscore form from [OPERATOR_MONITORING_SPEC.md](OPERATOR_MONITORING_SPEC.md) **§2**.

## 1. `replayt.workflow.run.outcomes_total` (counter)

**Purpose:** Throughput and failure rate of completed workflow runs ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5**).

**Labels:** `outcome` (`success` / `failure`), `workflow_id`; optional `run_id`. Keep `workflow_id` to a stable, small set per deployment; do not chart or alert on high-cardinality `run_id` by default ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5.4**, **§6.6**).

Counters only increase. In Prometheus, use **`rate()`** or **`increase()`** over a range window (for example `5m`) rather than raw counts for dashboards and alerts.

**Example PromQL** (adjust metric names if your scrape differs):

```promql
# Completed runs per second by workflow and outcome
sum by (workflow_id, outcome) (rate(replayt_workflow_run_outcomes_total[5m]))

# Failure ratio per workflow (0–1)
sum by (workflow_id) (rate(replayt_workflow_run_outcomes_total{outcome="failure"}[5m]))
/
clamp_min(
  sum by (workflow_id) (rate(replayt_workflow_run_outcomes_total[5m])),
  1e-9
)
```

For a **global** failure ratio (one number across all workflows), drop `sum by (workflow_id)` and aggregate in one layer; use that only when a single aggregate matches your SLO and traffic mix.

## 2. `replayt.workflow.run.duration_ms` (histogram)

**Purpose:** Run duration in milliseconds ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5**).

OpenTelemetry histograms usually become Prometheus **`_bucket`**, **`_sum`**, and **`_count`** series. The bucket label is often **`le`**. Confirm on scrape.

**Example PromQL** (classic histogram layout):

```promql
# Approximate p95 run duration in ms by workflow
histogram_quantile(
  0.95,
  sum by (workflow_id, le) (
    rate(replayt_workflow_run_duration_ms_bucket[5m])
  )
)
```

**If your backend does not expose Prometheus histogram buckets:** use that platform’s native view of OpenTelemetry histogram or distribution metrics (for example a vendor “metrics explorer” filtered on the exported duration instrument). Follow the vendor doc for **percentiles** or **heatmaps** from OTLP histogram export.

**Exemplars:** optional; only if policy allows ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5.6**, [SECURITY_REDACTION.md](SECURITY_REDACTION.md)).

## 3. `replayt.exporter.errors_total` (counter)

**Purpose:** Export-path health ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5**, **§5.3**).

**Normalized `error_type` values:** `export_failed`, `serialization_error`, `timeout`, `unknown`. Any other value is stored as `unknown` in this package.

Prefer alerts on **sustained** error rate or **non-zero increase** over a window you tune, not every single scrape blip, unless you explicitly want high sensitivity.

**Example PromQL:**

```promql
sum by (error_type) (rate(replayt_exporter_errors_total[5m]))
```

Optional breakdown by `workflow_id` when that label stays low-cardinality.

## 4. Grafana panels (minimum set)

These four panel ideas can live on one dashboard or several. Exact JSON is optional; type, query source, and labels matter.

| Panel intent | Query source | Notes |
| ------------ | ------------- | ----- |
| **Run rate / outcomes** | §1 above | Time series: lines or stacked series for `outcome`, split or filtered by `workflow_id`. |
| **Failure ratio** | §1 failure ratio | Stat or time series; compare to a threshold you set from baseline traffic. |
| **Latency (p95 or heatmap)** | §2 | Time series from `histogram_quantile`, or a native histogram heatmap if your datasource supports it. |
| **Exporter errors** | §3 | Time series by `error_type`. |

## 5. Alert starting points (tune per deployment)

Treat these as **defaults to adjust** using your traffic baseline, SLO, and acceptable noise.

1. **Failure ratio** — Fire when the §1 failure ratio over **`15m`** exceeds **N%** for a chosen `workflow_id` (or a global aggregate if appropriate). Set **N** from history (for example weekly p99 of the ratio plus headroom). Empty or very low traffic can make ratios noisy; use a `for:` delay or a minimum rate filter if needed.

2. **Exporter errors** — Either alert when `increase(replayt_exporter_errors_total[5m]) > 0` (strict), or when `rate(replayt_exporter_errors_total[5m])` stays above a small epsilon for **`10m`** (fewer flakes). Sustained errors mean lost or delayed telemetry.

3. **Latency** — Fire when the §2 **p95** (or your chosen quantile) for a **workflow-specific** threshold in milliseconds holds for **`15m`**. Thresholds are not universal; derive them from baselines per `workflow_id`.

**Investigation with traces:** When metrics spike, use traces filtered on span name **`replayt.workflow.run`** and attributes such as **`replayt.workflow.outcome`**, **`replayt.workflow.failure.category`**, and **`replayt.workflow.error.type`** ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§6**). This runbook does not duplicate the full trace spec.

## 6. Non-goals

Basic wiring of dashboards and alerts should not require reading `tracing.py`. Implementation detail and API contracts stay in source and [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md). When metric names or labels change in a release, update [CHANGELOG.md](../CHANGELOG.md) and [OPERATOR_MONITORING_SPEC.md](OPERATOR_MONITORING_SPEC.md) together with code, per project design principles.

## Related documents

- [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5–§6** — Metrics and traces.
- [OPERATOR_MONITORING_SPEC.md](OPERATOR_MONITORING_SPEC.md) — Full spec and acceptance mapping.
- [SECURITY_REDACTION.md](SECURITY_REDACTION.md) — What must not appear in telemetry attributes.
