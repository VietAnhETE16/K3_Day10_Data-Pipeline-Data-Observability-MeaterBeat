from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(
    df: pd.DataFrame,
    settings: Settings,
    report_name: str,
) -> dict[str, Any]:
    """Evaluate completeness, uniqueness, and freshness from actual row values."""
    total_rows = len(df)
    required_text_columns = ("paper_id", "title", "summary")

    missing_by_column: dict[str, int] = {}
    for column in required_text_columns:
        if column not in df.columns:
            missing_by_column[column] = total_rows
            continue
        values = df[column].astype("string")
        missing_by_column[column] = int((values.isna() | values.str.strip().eq("")).sum())

    if "summary" in df.columns:
        summaries = df["summary"].astype("string").fillna("")
        short_summaries = int(summaries.str.len().lt(100).sum())
    else:
        short_summaries = total_rows
    completeness_passed = (
        total_rows > 0
        and sum(missing_by_column.values()) == 0
        and short_summaries == 0
    )

    if "paper_id" in df.columns:
        paper_ids = df["paper_id"].astype("string").fillna("").str.strip()
        duplicate_rows = int(paper_ids[paper_ids.ne("")].duplicated(keep=False).sum())
    else:
        duplicate_rows = total_rows
    uniqueness_passed = total_rows > 0 and duplicate_rows == 0

    if "age_days" in df.columns:
        ages = pd.to_numeric(df["age_days"], errors="coerce")
        missing_age_rows = int(ages.isna().sum())
        future_rows = int(ages.lt(0).fillna(False).sum())
        stale_rows = int(ages.gt(settings.freshness_threshold_days).fillna(False).sum())
    else:
        missing_age_rows = total_rows
        future_rows = 0
        stale_rows = 0
    freshness_passed = (
        total_rows > 0
        and missing_age_rows == 0
        and future_rows == 0
        and stale_rows == 0
    )

    checks = [
        {
            "name": "completeness",
            "status": "PASS" if completeness_passed else "FAIL",
            "passed": completeness_passed,
            "observed": {
                "total_rows": total_rows,
                "missing_by_column": missing_by_column,
                "summary_under_100_rows": short_summaries,
            },
        },
        {
            "name": "uniqueness",
            "status": "PASS" if uniqueness_passed else "FAIL",
            "passed": uniqueness_passed,
            "observed": {
                "total_rows": total_rows,
                "duplicate_paper_id_rows": duplicate_rows,
            },
        },
        {
            "name": "freshness",
            "status": "PASS" if freshness_passed else "FAIL",
            "passed": freshness_passed,
            "observed": {
                "threshold_days": settings.freshness_threshold_days,
                "missing_age_rows": missing_age_rows,
                "future_dated_rows": future_rows,
                "stale_rows": stale_rows,
            },
        },
    ]
    passed = all(check["passed"] for check in checks)
    report = {
        "report_name": report_name,
        "status": "PASS" if passed else "FAIL",
        "passed": passed,
        "total_rows": total_rows,
        "checks": checks,
    }
    write_json(settings.paths.quality_dir / f"{report_name}.json", report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build a persisted freshness summary from publication dates and ages."""
    total_rows = len(df)
    published = pd.to_datetime(
        df["published"] if "published" in df.columns else pd.Series(dtype="object"),
        errors="coerce",
        utc=True,
    )
    ages = pd.to_numeric(
        df["age_days"] if "age_days" in df.columns else pd.Series(dtype="float64"),
        errors="coerce",
    )
    valid_published = published.dropna()
    stale_rows = int(ages.gt(settings.freshness_threshold_days).fillna(False).sum())
    missing_age_rows = total_rows - int(ages.notna().sum())
    future_rows = int(ages.lt(0).fillna(False).sum())
    is_fresh = (
        total_rows > 0
        and len(valid_published) == total_rows
        and missing_age_rows == 0
        and future_rows == 0
        and stale_rows == 0
    )
    report = {
        "latest_published": (
            valid_published.max().date().isoformat() if not valid_published.empty else None
        ),
        "oldest_published": (
            valid_published.min().date().isoformat() if not valid_published.empty else None
        ),
        "freshness_threshold_days": settings.freshness_threshold_days,
        "stale_rows": stale_rows,
        "missing_age_rows": missing_age_rows,
        "future_dated_rows": future_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh,
        "status": "PASS" if is_fresh else "FAIL",
    }
    write_json(report_path, report)
    return report
