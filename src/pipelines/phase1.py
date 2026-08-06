from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run the clean-data baseline pipeline and persist all evidence artifacts."""
    settings = load_settings()

    should_fetch = settings.refresh_source or not settings.paths.raw_records_json.exists()
    if should_fetch:
        records = fetch_source_records(settings)
        source_mode = "fetched"
    else:
        records = load_raw_records(settings.paths.raw_records_json)
        source_mode = "cached raw snapshot"
    print(f"[phase1] source={source_mode}; raw_records={len(records)}")

    clean_df = build_clean_dataframe(records, now_utc())
    if clean_df.empty:
        raise RuntimeError("Cleaning produced no valid records; baseline cannot continue.")
    print(f"[phase1] clean_records={len(clean_df)}")

    index = LocalEmbeddingIndex.build(
        clean_df,
        settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"[phase1] index_documents={len(index.documents)}")

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        test_set = build_test_set(clean_df, settings.paths.eval_testset)
        print(f"[phase1] test_set=generated; samples={len(test_set)}")
    else:
        print("[phase1] test_set=frozen snapshot")

    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    quality = run_data_quality_checks(clean_df, settings, "baseline_quality")
    freshness = build_freshness_report(
        clean_df,
        settings,
        settings.paths.freshness_report,
    )
    source_summary = {
        "source": settings.source_api,
        "source_mode": source_mode,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "raw_records": len(records),
        "clean_records": len(clean_df),
        "evaluation_samples": evaluation.summary["samples"],
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )
    print(
        "[phase1] completed; "
        f"retrieval_hit_rate={evaluation.summary['retrieval_hit_rate']:.4f}; "
        f"quality={quality['status']}; freshness={freshness['status']}"
    )
