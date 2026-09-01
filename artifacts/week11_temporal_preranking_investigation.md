# Final bounded retrieval investigation: pre-ranking temporal filter

## Fixed intervention

The existing strict temporal rule was retained without modification: an eCourts authority is eligible only when its exact decision year is strictly earlier than the ILDC query year. The sole intervention was to apply that predicate in the SQLite FTS candidate relation before `ORDER BY bm25(...) LIMIT 100`. Same-year, future-year, missing-date, audited-duplicate, and direct-content self-match rules remain in force.

This is the last retrieval configuration change for the project. The adopted configuration is `week11-bm25-salient-terms-preranked-temporal-v3`.

## Frozen 30-case answer-key comparison

| Measure | Post-ranking baseline | Pre-ranking temporal filter | Change |
|---|---:|---:|---:|
| Recall@5 | 5/30 (0.166667) | 12/30 (0.400000) | +7 cases |
| Recall@100 | 12/30 (0.400000) | 15/30 (0.500000) | +3 cases |
| Expected authority retrieved and selected | 11/30 | 12/30 | +1 case |
| Retrieved but not selected | 1/30 | 3/30 | +2 cases |
| Expected authority absent at k=100 | 18/30 | 15/30 | -3 cases |
| Regressions among the original 12 Recall@100 successes | -- | 0 | none |
| Citation grounding / provenance / temporal violations | 135/135 / 135/135 / 0 | 150/150 / 150/150 / 0 | preserved |

The final candidate log contains 3,000/3,000 eligible candidates: FEER is 0/3,000 and FCER is 0/150. The preserved post-ranking baseline had FEER 1,712/2,743 = 0.624134, plus 267 same-year candidates excluded as ambiguous. The prior FEER finding was therefore a real capacity constraint, not merely a reporting statistic.

## Requested case checks

- `2013_35` remains absent at k=100 after pre-ranking; its earlier 79 eligible raw candidates were already sufficient to show that temporal-pool size alone does not determine retrieval success.
- `1980_105` remains retrieved and selected, but improves from outside top-5 to Recall@5 success. Its earlier success despite only three eligible raw candidates confirms that case-specific lexical relevance also matters.

## Dev-only consistency check (k=100)

| Dev case | Previous rank | Final pre-ranking rank |
|---|---:|---:|
| `1980_104` | 58 | 28 |
| `1982_186` | absent | 100 |
| `1984_62` | 40 | 3 |
| `1986_70` | absent | absent |
| `1988_238` | 64 | 4 |
| `1990_651` | 92 | 48 |
| `1992_137` | 67 | 17 |
| `1992_464` | 69 | 28 |
| `1993_66` | absent | absent |

Dev retrieval improves from 6/9 to 7/9 authorities at k=100. This check was run only for consistency after the real-cohort comparison; no additional variant was attempted.

## Decision

Adopt pre-ranking temporal filtering. It improves both Recall@5 and Recall@100, increases the selected expected-authority count, preserves all 12 original retrieval successes, and retains perfect grounding, provenance, and temporal-integrity checks. Remaining misses demonstrate that lexical/relevance limitations persist, but the post-ranking temporal-ordering dilution was a material, correctable contributor.
