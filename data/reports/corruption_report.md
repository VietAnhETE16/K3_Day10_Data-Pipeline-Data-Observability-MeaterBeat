# Data Corruption and Repair Comparison Report

This report compares the performance and observability signals of the RAG system across three states: Baseline (clean data), Corrupted (with controlled data errors), and Repaired (fully recovered).

## Overall Summary Table

| Metric / Signal | Baseline | Corrupted | Repaired |
| :--- | :---: | :---: | :---: |
| **Data Quality Status** | **PASS** | **FAIL** | **PASS** |
| **Data Freshness Status** | **PASS** | **FAIL** | **PASS** |
| **Total Rows** | 20 | 25 | 24 |
| **RAG Samples** | 20 | 20 | 20 |
| **Retrieval Hit Rate** | 1.0000 | 1.0000 | 1.0000 |
| **Mean Token F1** | 1.0000 | 0.9000 | 1.0000 |
| **LLM Judge Accuracy** | 1.0000 | 0.9000 | 1.0000 |
| **Mean LLM Judge Score** | 5 | 4.7000 | 5 |

## Data Quality Details

### Corrupted State Quality Checks
- Status: **FAIL**
- Checks details:
*   **completeness**: **FAIL** (total_rows=25, missing_by_column={'paper_id': 0, 'title': 0, 'summary': 1}, summary_under_100_rows=1)
*   **uniqueness**: **FAIL** (total_rows=25, duplicate_paper_id_rows=2)
*   **freshness**: **FAIL** (threshold_days=180, missing_age_rows=0, future_dated_rows=0, stale_rows=1)

### Repaired State Quality Checks
- Status: **PASS**
- Checks details:
*   **completeness**: **PASS** (total_rows=24, missing_by_column={'paper_id': 0, 'title': 0, 'summary': 0}, summary_under_100_rows=0)
*   **uniqueness**: **PASS** (total_rows=24, duplicate_paper_id_rows=0)
*   **freshness**: **PASS** (threshold_days=180, missing_age_rows=0, future_dated_rows=0, stale_rows=0)

## Data Freshness Details

### Corrupted State Freshness
- Stale Rows: **1**
- Is Fresh: **False**

### Repaired State Freshness
- Stale Rows: **0**
- Is Fresh: **True**
