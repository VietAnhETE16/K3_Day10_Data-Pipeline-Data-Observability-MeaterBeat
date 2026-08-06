import json
from pathlib import Path

import pandas as pd

from ingestion.corruption import corrupt_clean_dataframe


def test_corrupt_clean_dataframe_writes_log(tmp_path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "paper_id": "p1",
                "title": "Agentic Retrieval for LLMs",
                "summary": "A detailed summary about agentic retrieval and large language models.",
                "published": "2026-08-01",
                "age_days": 10,
                "text_for_embedding": "Title: Agentic Retrieval for LLMs | Summary: ...",
            },
            {
                "paper_id": "p2",
                "title": "RAG Evaluation Benchmarks",
                "summary": "A detailed summary about evaluation benchmarks for retrieval augmented generation.",
                "published": "2026-07-01",
                "age_days": 40,
                "text_for_embedding": "Title: RAG Evaluation Benchmarks | Summary: ...",
            },
        ]
    )

    output_log_path = tmp_path / "corruption_log.json"
    corrupted = corrupt_clean_dataframe(df, output_log_path)

    assert not corrupted.empty
    assert output_log_path.exists()
    payload = json.loads(output_log_path.read_text(encoding="utf-8"))
    assert payload["summary"]["row_count"] == len(df)
    assert payload["applied_actions"]
