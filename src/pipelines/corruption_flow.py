from __future__ import annotations

import pandas as pd
from core.config import load_settings
from core.utils import now_utc, write_csv, ensure_parent
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report


def main() -> None:
    # 1. Load settings and clean dataset
    settings = load_settings()
    print("Loading clean dataset...")
    df = pd.read_csv(settings.paths.clean_csv)

    # 2. Run quality checks on baseline data
    print("Running baseline quality and freshness checks...")
    run_data_quality_checks(df, settings, "baseline_quality")
    build_freshness_report(df, settings, settings.paths.freshness_report)

    # 3. Create corrupted dataframe
    print("Generating corrupted data...")
    corrupted_df = corrupt_clean_dataframe(df, settings.paths.corruption_log)

    # 4. Save corrupted artifacts
    print("Saving corrupted clean artifacts...")
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    ensure_parent(settings.paths.corrupted_clean_json)
    corrupted_df.to_json(
        settings.paths.corrupted_clean_json,
        orient="records",
        indent=2,
        force_ascii=False
    )

    # 5. Rebuild index and evaluate corrupted state
    print("Rebuilding ChromaDB index for corrupted data...")
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json
    )

    print("Evaluating corrupted pipeline...")
    evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers
    )

    # 6. Run quality checks/freshness on corrupted data
    print("Running quality and freshness checks on corrupted data...")
    run_data_quality_checks(corrupted_df, settings, "corrupted_quality")
    build_freshness_report(corrupted_df, settings, settings.paths.quality_dir / "corrupted_freshness_report.json")

    # 7. Repair: Load raw records, rerun cleaning
    print("Repairing dataset from raw records...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, now_utc())

    # Save repaired clean artifacts
    print("Saving repaired clean artifacts...")
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    ensure_parent(settings.paths.repaired_clean_json)
    repaired_df.to_json(
        settings.paths.repaired_clean_json,
        orient="records",
        indent=2,
        force_ascii=False
    )

    # 8. Rebuild index and evaluate repaired state
    print("Rebuilding ChromaDB index for repaired data...")
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json
    )

    print("Evaluating repaired pipeline...")
    evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers
    )

    # 9. Run quality checks/freshness on repaired data
    print("Running quality and freshness checks on repaired data...")
    run_data_quality_checks(repaired_df, settings, "repaired_quality")
    build_freshness_report(repaired_df, settings, settings.paths.quality_dir / "repaired_freshness_report.json")

    print("Pipeline completed!")
    print("NOTE: Report generation has been skipped as requested by the user.")
