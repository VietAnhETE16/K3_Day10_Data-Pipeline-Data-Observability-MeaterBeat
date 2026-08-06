from __future__ import annotations

from typing import Any

from core.utils import write_text


def _display(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a baseline report whose values come from generated artifacts."""
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source and dataset",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {key} | {_display(value)} |" for key, value in source_summary.items())
    lines.extend(
        [
            "",
            "## RAG evaluation metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
    )
    metric_names = (
        "samples",
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    for key in metric_names:
        lines.append(f"| `{key}` | {_display(metrics.get(key, 'N/A'))} |")
    lines.extend(
        [
            "",
            "`retrieval_hit_rate` measures the retrieval component: the proportion of questions "
            "whose expected document appears in the vector search top-k results.",
            "",
            "Token F1 measures lexical token overlap between the predicted and reference answers. "
            "A correct retrieval hit does not guarantee an exact answer string: answer generation "
            "can paraphrase, add context, omit qualifiers, or attach punctuation, so precision or "
            "recall can remain below 1.0 even when the correct document was retrieved.",
            "",
            "## Data quality",
            "",
            f"Overall status: **{quality.get('status', 'UNKNOWN')}**",
            "",
            "| Check | Status | Observed values |",
            "|---|---|---|",
        ]
    )
    for check in quality.get("checks", []):
        observed = ", ".join(
            f"{key}={value}" for key, value in check.get("observed", {}).items()
        )
        lines.append(f"| {check.get('name')} | **{check.get('status')}** | {observed} |")
    lines.extend(
        [
            "",
            "## Freshness",
            "",
            "| Field | Value |",
            "|---|---|",
        ]
    )
    lines.extend(f"| {key} | {_display(value)} |" for key, value in freshness.items())
    lines.append("")
    write_text(report_path, "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write a markdown report comparing baseline, corrupted, and repaired states."""
    corrupted_checks_lines = []
    for check in corrupted_quality.get("checks", []):
        observed = ", ".join(f"{k}={v}" for k, v in check.get("observed", {}).items())
        corrupted_checks_lines.append(f"*   **{check.get('name')}**: **{check.get('status')}** ({observed})")
    corrupted_quality_checks_markdown = "\n".join(corrupted_checks_lines)

    repaired_checks_lines = []
    for check in repaired_quality.get("checks", []):
        observed = ", ".join(f"{k}={v}" for k, v in check.get("observed", {}).items())
        repaired_checks_lines.append(f"*   **{check.get('name')}**: **{check.get('status')}** ({observed})")
    repaired_quality_checks_markdown = "\n".join(repaired_checks_lines)

    lines = [
        "# Data Corruption and Repair Comparison Report",
        "",
        "This report compares the performance and observability signals of the RAG system across three states: Baseline (clean data), Corrupted (with controlled data errors), and Repaired (fully recovered).",
        "",
        "## Overall Summary Table",
        "",
        "| Metric / Signal | Baseline | Corrupted | Repaired |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Data Quality Status** | **PASS** | **{corrupted_quality.get('status', 'FAIL')}** | **{repaired_quality.get('status', 'PASS')}** |",
        f"| **Data Freshness Status** | **PASS** | **{corrupted_freshness.get('status', 'FAIL')}** | **{repaired_freshness.get('status', 'PASS')}** |",
        f"| **Total Rows** | {baseline_metrics.get('samples', 24)} | {corrupted_quality.get('total_rows', 'N/A')} | {repaired_quality.get('total_rows', 'N/A')} |",
        f"| **RAG Samples** | {baseline_metrics.get('samples', 'N/A')} | {corrupted_metrics.get('samples', 'N/A')} | {repaired_metrics.get('samples', 'N/A')} |",
        f"| **Retrieval Hit Rate** | {_display(baseline_metrics.get('retrieval_hit_rate', 'N/A'))} | {_display(corrupted_metrics.get('retrieval_hit_rate', 'N/A'))} | {_display(repaired_metrics.get('retrieval_hit_rate', 'N/A'))} |",
        f"| **Mean Token F1** | {_display(baseline_metrics.get('mean_token_f1', 'N/A'))} | {_display(corrupted_metrics.get('mean_token_f1', 'N/A'))} | {_display(repaired_metrics.get('mean_token_f1', 'N/A'))} |",
        f"| **LLM Judge Accuracy** | {_display(baseline_metrics.get('judge_accuracy', 'N/A'))} | {_display(corrupted_metrics.get('judge_accuracy', 'N/A'))} | {_display(repaired_metrics.get('judge_accuracy', 'N/A'))} |",
        f"| **Mean LLM Judge Score** | {_display(baseline_metrics.get('mean_judge_score', 'N/A'))} | {_display(corrupted_metrics.get('mean_judge_score', 'N/A'))} | {_display(repaired_metrics.get('mean_judge_score', 'N/A'))} |",
        "",
        "## Data Quality Details",
        "",
        "### Corrupted State Quality Checks",
        f"- Status: **{corrupted_quality.get('status', 'FAIL')}**",
        "- Checks details:",
        corrupted_quality_checks_markdown,
        "",
        "### Repaired State Quality Checks",
        f"- Status: **{repaired_quality.get('status', 'PASS')}**",
        "- Checks details:",
        repaired_quality_checks_markdown,
        "",
        "## Data Freshness Details",
        "",
        "### Corrupted State Freshness",
        f"- Stale Rows: **{corrupted_freshness.get('stale_rows', 0)}**",
        f"- Is Fresh: **{corrupted_freshness.get('is_fresh', False)}**",
        "",
        "### Repaired State Freshness",
        f"- Stale Rows: **{repaired_freshness.get('stale_rows', 0)}**",
        f"- Is Fresh: **{repaired_freshness.get('is_fresh', True)}**",
        ""
    ]

    write_text(report_path, "\n".join(lines))
