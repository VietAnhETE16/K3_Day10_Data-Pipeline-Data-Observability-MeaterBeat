from __future__ import annotations

import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    import json
    from pathlib import Path
    from core.utils import write_json

    # 1. Load the frozen test set to identify paper IDs to corrupt
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parents[1]
    test_set_path = project_root / "data" / "eval" / "test_set.json"

    test_doc_ids = []
    if test_set_path.exists():
        with open(test_set_path, "r", encoding="utf-8") as f:
            test_set = json.load(f)
            for item in test_set:
                test_doc_ids.extend(item.get("ground_truth_doc_ids", []))
    test_doc_ids = sorted(list(set(test_doc_ids)))

    corrupted_df = df.copy()
    corruption_log = {"corrupted_records": []}

    # Case 1: Blank Summary
    if len(test_doc_ids) > 0:
        target_id_1 = test_doc_ids[0]
        idx = corrupted_df[corrupted_df["paper_id"] == target_id_1].index
        if not idx.empty:
            orig_val = corrupted_df.loc[idx[0], "summary"]
            corrupted_df.loc[idx[0], "summary"] = ""
            corruption_log["corrupted_records"].append({
                "paper_id": target_id_1,
                "corruption_type": "blank_summary",
                "original_value": orig_val,
                "new_value": ""
            })

    # Case 2: Stale Date (change publication date to 2000-01-01)
    if len(test_doc_ids) > 1:
        target_id_2 = test_doc_ids[1]
        idx = corrupted_df[corrupted_df["paper_id"] == target_id_2].index
        if not idx.empty:
            orig_val = corrupted_df.loc[idx[0], "published"]
            corrupted_df.loc[idx[0], "published"] = "2000-01-01"
            corrupted_df.loc[idx[0], "age_days"] = 9700
            corruption_log["corrupted_records"].append({
                "paper_id": target_id_2,
                "corruption_type": "stale_date",
                "original_value": orig_val,
                "new_value": "2000-01-01"
            })

    # Case 3: Duplicates (duplicate a row and keep the same ID)
    if len(test_doc_ids) > 2:
        target_id_3 = test_doc_ids[2]
        idx = corrupted_df[corrupted_df["paper_id"] == target_id_3].index
        if not idx.empty:
            row_to_dup = corrupted_df.loc[idx[0]].copy()
            corrupted_df = pd.concat([corrupted_df, pd.DataFrame([row_to_dup])], ignore_index=True)
            corruption_log["corrupted_records"].append({
                "paper_id": target_id_3,
                "corruption_type": "duplicate_record",
                "original_value": "single_row",
                "new_value": "duplicated_row"
            })

    # Case 4: Add Noise to text_for_embedding
    if len(test_doc_ids) > 3:
        target_id_4 = test_doc_ids[3]
        idx = corrupted_df[corrupted_df["paper_id"] == target_id_4].index
        if not idx.empty:
            orig_val = corrupted_df.loc[idx[0], "text_for_embedding"]
            noise_text = " [XyZ#@!123_RANDOM_NOISE_CORRUPTING_THE_TEXT] "
            corruption_log["corrupted_records"].append({
                "paper_id": target_id_4,
                "corruption_type": "noise_injection",
                "original_value": orig_val,
                "new_value": noise_text + orig_val
            })

    # Rebuild text_for_embedding for all records
    for i in corrupted_df.index:
        paper_id = corrupted_df.loc[i, "paper_id"]
        title = corrupted_df.loc[i, "title"]
        authors_joined = corrupted_df.loc[i, "authors_joined"]
        summary = corrupted_df.loc[i, "summary"]
        text_for_embed = f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"
        if len(test_doc_ids) > 3 and paper_id == test_doc_ids[3]:
            text_for_embed = " [XyZ#@!123_RANDOM_NOISE_CORRUPTING_THE_TEXT] " + text_for_embed
        corrupted_df.loc[i, "text_for_embedding"] = text_for_embed

    # Write log to output_log_path
    write_json(Path(output_log_path), corruption_log)

    return corrupted_df
