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
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    raise NotImplementedError("Student task: implement corruption comparison report.")
