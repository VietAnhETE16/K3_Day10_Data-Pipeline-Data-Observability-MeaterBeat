# Phase 1 Baseline Report

## Source and dataset

| Field | Value |
|---|---|
| source | Crossref REST API |
| source_mode | cached raw snapshot |
| query | agentic retrieval augmented generation large language model |
| filter | from-pub-date:2026-02-07,has-abstract:true |
| raw_records | 24 |
| clean_records | 24 |
| evaluation_samples | 20 |

## RAG evaluation metrics

| Metric | Value |
|---|---:|
| `samples` | 20 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5 |

`retrieval_hit_rate` measures the retrieval component: the proportion of questions whose expected document appears in the vector search top-k results.

Token F1 measures lexical token overlap between the predicted and reference answers. A correct retrieval hit does not guarantee an exact answer string: answer generation can paraphrase, add context, omit qualifiers, or attach punctuation, so precision or recall can remain below 1.0 even when the correct document was retrieved.

## Data quality

Overall status: **PASS**

| Check | Status | Observed values |
|---|---|---|
| completeness | **PASS** | total_rows=24, missing_by_column={'paper_id': 0, 'title': 0, 'summary': 0}, summary_under_100_rows=0 |
| uniqueness | **PASS** | total_rows=24, duplicate_paper_id_rows=0 |
| freshness | **PASS** | threshold_days=180, missing_age_rows=0, future_dated_rows=0, stale_rows=0 |

## Freshness

| Field | Value |
|---|---|
| latest_published | 2026-08-01 |
| oldest_published | 2026-02-12 |
| freshness_threshold_days | 180 |
| stale_rows | 0 |
| missing_age_rows | 0 |
| future_dated_rows | 0 |
| total_rows | 24 |
| is_fresh | True |
| status | PASS |
