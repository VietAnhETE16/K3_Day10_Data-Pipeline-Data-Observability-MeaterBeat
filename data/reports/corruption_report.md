# Corruption Impact Report

## Summary

This report compares the baseline, corrupted, and repaired states using metrics and data-quality signals generated from the same evaluation set.

## Metric changes

| Metric | Baseline | Corrupted | Repaired | Change | Evidence |
|---|---:|---:|---:|---:|---|
| retrieval_hit_rate | 1.0000 | 0.9000 | 1.0000 | -0.1000 | drop=-0.1000; recovery=0.1000 |
| mean_token_f1 | 1.0000 | 0.9114 | 1.0000 | -0.0886 | drop=-0.0886; recovery=0.0886 |
| judge_accuracy | 1.0000 | 0.9000 | 1.0000 | -0.1000 | drop=-0.1000; recovery=0.1000 |
| mean_judge_score | 5 | 4.6000 | 5 | -0.4000 | drop=-0.4000; recovery=0.4000 |

## Quality and freshness signals

| Signal | Baseline | Corrupted | Repaired | Interpretation |
|---|---|---|---|---|
| quality_status | PASS | FAIL | PASS | Quality gate status |
| freshness_status | PASS | FAIL | PASS | Freshness gate status |
| stale_rows | 0 | 1 | 0 | Rows older than the freshness threshold |

## Corruption evidence

- Applied actions: 7
- Blank summaries: 1
- Duplicate rows: 1
- Stale publication rows: 1

## Signals that stayed unchanged

The following signals are explicitly recorded as unchanged so the report does not overstate the impact of corruption:

- Evaluation sample count stayed the same across baseline, corrupted, and repaired runs.
