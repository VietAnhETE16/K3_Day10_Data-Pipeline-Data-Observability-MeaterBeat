from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


TEST_SET_SIZE = 20


def _representative_indices(row_count: int, sample_count: int) -> list[int]:
    """Choose deterministic positions spread across the cleaned corpus."""
    if sample_count == 1:
        return [0]
    return [round(index * (row_count - 1) / (sample_count - 1)) for index in range(sample_count)]


def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict[str, Any]]:
    """Build and persist a deterministic factual evaluation set."""
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "published",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Clean dataframe is missing required columns: {missing}")

    eligible = df.copy()
    for column in required_columns:
        eligible[column] = eligible[column].fillna("").astype(str).str.strip()
    eligible = eligible[
        eligible["paper_id"].ne("")
        & eligible["title"].ne("")
        & eligible["summary"].ne("")
        & eligible["authors_joined"].ne("")
        & eligible["published"].ne("")
    ].reset_index(drop=True)

    if len(eligible) < 5:
        raise ValueError("At least 5 complete clean documents are required to build the test set.")

    sample_count = min(TEST_SET_SIZE, len(eligible))
    selected = eligible.iloc[_representative_indices(len(eligible), sample_count)]
    
    kinds = ["authors", "summary", "date"]
    question_kinds = [kinds[i % len(kinds)] for i in range(sample_count)]

    test_set: list[dict[str, Any]] = []
    for number, (kind, (_, row)) in enumerate(
        zip(question_kinds, selected.iterrows(), strict=False),
        start=1,
    ):
        title = row["title"]
        if kind == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = row["authors_joined"]
        elif kind == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = row["published"]
        else:
            question = f"What is described in the paper '{title}'?"
            ground_truth = first_sentence(row["summary"])

        test_set.append(
            {
                "id": f"q{number}",
                "question_type": "factual",
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [row["paper_id"]],
            }
        )

    write_json(output_path, test_set)
    return test_set


if __name__ == "__main__":
    from core.config import load_settings
    settings = load_settings()
    df = pd.read_csv(settings.paths.clean_csv)
    build_test_set(df, settings.paths.eval_testset)
    print(f"Generated test set with {TEST_SET_SIZE} questions at {settings.paths.eval_testset}")
