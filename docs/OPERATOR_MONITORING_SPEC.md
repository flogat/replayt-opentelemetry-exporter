# Operator monitoring: dashboards and alerts for canonical metrics

This document is the **specification** for backlog item *Document operator dashboards for canonical metrics*. It turns that backlog into **testable documentation obligations** for the **Builder** phase. Operators should be able to wire **Prometheus-compatible** monitoring and **Grafana-style** panels using this package’s **canonical instruments** without reading `tracing.py`.

**Normative contracts** for instrument names, attributes, cardinality, and trace signals live in **[PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) §5–§6**, with **OpenTelemetry semantic convention alignment** (metrics, resource, traces) in **§5.7** and **§6.8**. This spec adds **observability-backend recipes** (PromQL, panel intent, alert starting points) that MUST stay aligned with those sections.

## 1. Purpose and audience

| Audience | Need |
| -------- | ---- |
| **Operators** | Map exported metrics to useful dashboards and alerts in production. |
| **Integrators** | Know which labels are safe for grouping and which dimensions explode cardinality. |

This package does **not** mandate a vendor. Recipes below use **Prometheus**-style metric and label names; other backends SHOULD translate equivalently.

## 2. Metric and label names after export

Canonical **logical** instrument names are defined in [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5** (for example `replayt.workflow.run.outcomes_total`).

Many Prometheus scrapes expose OpenTelemetry metrics with **dots replaced by underscores** and **OTel attribute keys** mapped to **Prometheus label names** (often unchanged). The shipped operator runbook MUST:

1. State that operators MUST confirm the exact **series names and label keys** on their scrape target or in their vendor’s “metrics explorer” before copying queries verbatim.
2. Use **one** consistent naming style in examples (this repository recommends **underscore** Prometheus-style names in PromQL blocks below as the default assumption).

**Recommended example base names for PromQL** (verify in your environment):

| Canonical instrument (§5) | Example Prometheus series name |
| ------------------------- | ------------------------------ |
| `replayt.workflow.run.outcomes_total` | `replayt_workflow_run_outcomes_total` |
| `replayt.workflow.run.duration_ms` | `replayt_workflow_run_duration_ms` |
| `replayt.exporter.errors_total` | `replayt_exporter_errors_total` |

Label semantics and allowed cardinalities: [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5.2–§5.4** and **§6.6** (traces). **Do not** use `run_id` as a routine dashboard or alert grouping dimension when it is high-cardinality (§5.4, §6.6).

## 3. Deliverable shape (Builder)

The backlog is satisfied for **documentation** when **both** of the following hold:

1. **`docs/OPERATOR_RUNBOOK.md`** exists at the repository root’s `docs/` tree and is linked from the README **Metrics** section (or a short **Operator monitoring** subsection under it).
2. The runbook content meets **§4–§7** of this specification.

**Alternative (not preferred):** A README subsection of **at least** the same informational depth as §4–§7 MAY substitute for the standalone file only if the README section is explicitly called out in **§1.1** of [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) and the project layout table lists it. Prefer **`docs/OPERATOR_RUNBOOK.md`** for clarity.

## 4. Required runbook content by instrument

Each subsection MUST appear in `docs/OPERATOR_RUNBOOK.md` (or the README alternative). Wording MAY differ; **queries and label usage** MUST match the intent below and **§5–§6** of the public API spec.

### 4.1 `replayt.workflow.run.outcomes_total` (Counter)

**Purpose:** Throughput and failure rate of completed runs (see [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5**).

**Labels (normative):** `outcome` (`success` / `failure`), `workflow_id`; optional `run_id` — see cardinality rules in **§5.4**.

**Minimum documentation:**

- Explain that this is a **counter**; use **`rate()`** or **`increase()`** over a range window in Prometheus.
- Provide **at least one** PromQL example for:
  - **Runs per second** (or per minute) **by** `workflow_id` and `outcome`.
  - **Failure ratio** over a window: failures / (successes + failures), e.g. aggregated per `workflow_id` or globally with a note on when global is appropriate.
- Reference [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5.4** and **§6.6**: stable `workflow_id` set; do not chart high-cardinality `run_id` by default.

**Reference PromQL** (underscore metric name — adjust if your scrape differs):

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

### 4.2 `replayt.workflow.run.duration_ms` (Histogram)

**Purpose:** Latency of runs in milliseconds ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5**).

**Minimum documentation:**

- Explain that OpenTelemetry histograms typically map to Prometheus **bucket** (`_bucket`), **sum**, and **count** series; operators should use their backend’s preferred latency visualization (**heatmap**, **percentiles** from histograms, or native quantile support if the backend provides it).
- Provide **at least one** PromQL example for **p95 latency** (or equivalent) per `workflow_id`, using **histogram_quantile** if Prometheus buckets are present, **or** document the vendor-native alternative when buckets are not exposed.
- Reference **§5.6** (exemplars): optional; only when policy allows.

**Reference PromQL** (classic histogram layout; bucket label name may be `le` — confirm on scrape):

```promql
# Approximate p95 run duration in ms by workflow (Prometheus histogram)
histogram_quantile(
  0.95,
  sum by (workflow_id, le) (
    rate(replayt_workflow_run_duration_ms_bucket[5m])
  )
)
```

If the runbook targets a backend that does not expose Prometheus histogram buckets, it MUST still document **how** to chart run duration from this instrument using that backend’s docs (one concrete path).

### 4.3 `replayt.exporter.errors_total` (Counter)

**Purpose:** Export-path health ([PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5**, **§5.3** `error_type`).

**Minimum documentation:**

- List the **normalized** `error_type` values: `export_failed`, `serialization_error`, `timeout`, `unknown`.
- Provide **at least one** PromQL example: **rate of errors** summed or broken down by `error_type` (and optionally `workflow_id` when low-cardinality).
- Tie alerts to **sustained** error rate, not single spikes, unless the operator explicitly chooses high sensitivity.

**Reference PromQL:**

```promql
sum by (error_type) (rate(replayt_exporter_errors_total[5m]))
```

## 5. Grafana panels (minimum)

The runbook MUST describe **at least three** panel concepts (they may map to one dashboard or several):

| Panel intent | Suggested query source | Notes |
| ------------ | ---------------------- | ----- |
| **Run rate / outcomes** | §4.1 | Time series: stacked or separate lines for `outcome` per `workflow_id`. |
| **Failure ratio** | §4.1 | Stat or time series; warn when ratio exceeds a tunable threshold. |
| **Latency (p95 or heatmap)** | §4.2 | Time series or native histogram heatmap. |
| **Exporter errors** | §4.3 | Time series by `error_type`. |

Exact Grafana JSON is optional; **panel type + query + key labels** are required.

## 6. Alert thresholds (starting points)

Alerts MUST be documented as **starting points** to tune per deployment (traffic baseline, SLO, and cardinality). The runbook MUST include **at least**:

1. **Failure ratio** — Example: alert when failure ratio over **15m** exceeds **N%** for a given `workflow_id` (or global), with guidance to set **N** from historical baseline; cite §4.1 ratio query.
2. **Exporter errors** — Example: alert when `increase(replayt_exporter_errors_total[5m]) > 0` **or** when **rate** exceeds a small epsilon for **10m**, depending on noise tolerance; explain why sustained errors matter for telemetry gaps.
3. **Latency** — Example: alert when p95 from §4.2 exceeds a **workflow-specific** ms threshold for **15m**; state that thresholds are not universal.

Optional: link high failure rates or latency to **traces** using [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§6** (span name `replayt.workflow.run`, attributes `replayt.workflow.outcome`, `replayt.workflow.failure.category`) for investigation — without duplicating the full trace spec.

## 7. Non-goals and consistency

- The runbook MUST NOT require readers to open `tracing.py` for basic wiring; implementation details stay in code and [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md).
- When metric names or label keys change in a release, **CHANGELOG.md** and this spec’s reference examples MUST be updated in the same change set as the code (per design principles).

## 8. Acceptance summary

| Backlog acceptance criterion | Where satisfied |
| ---------------------------- | ---------------- |
| Map three canonical metrics to example PromQL and panel intent | **§4–§5**; implemented in **`docs/OPERATOR_RUNBOOK.md`** |
| Sane alert starting points | **§6**; implemented in the runbook |
| Label semantics and cardinality aligned with public API | **§2**, **§4**, pointers to [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5–§6** |
| Operators avoid reading `tracing.py` for standard monitoring | **§3** deliverable + **§7** |

## 9. Related documents

- [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md) **§5** — Metrics; **§6** — Traces for drill-down.
- [SECURITY_REDACTION.md](SECURITY_REDACTION.md) — What must not appear in attributes (metrics and spans).
- [README.md](../README.md) — Enable export, metrics summary, **Operator monitoring** link to [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md).
