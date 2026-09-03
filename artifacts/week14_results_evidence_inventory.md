# Week 14 Results Evidence Inventory

## Scope

Read-only consolidation of final results for report drafting; no inference, retrieval, evaluation, answer-key edit, or configuration change.

## Results available for report drafting

| Area | Population | Measured result | Permitted interpretation |
|---|---|---|---|
| Outcome prediction | 1,503 eligible fixed test cases | E1 accuracy 0.6134, macro F1 0.6123; corrected E2 accuracy 0.5968, macro F1 0.5924; majority accuracy 0.5017 | E1 leads corrected E2 on this frozen outcome task; both exceed majority accuracy. |
| Authority recovery and verified evidence | 30 answer-key cases; 150 displayed citations | Recall@5 0.40; Recall@100 0.50; 12 selected / 3 retrieved-not-selected / 15 absent; 150/150 displayed citations grounded, provenance-valid, and temporally eligible | Report verification quality separately from predefined-authority recovery. |
| Explanation-format review | 7 fixed paired cases; author self-review fallback | Structured preference 7/7; structured vs. unstructured source-clarity mean 4.57 vs. 2.71 | Descriptive author self-review only; not an independent human-review or legal-correctness result. |

## Mandatory reporting guards

- Keep the 1,503-case outcome-prediction population distinct from the 30-case source-verified answer-key subset and the 7-case self-review sample.
- Use only the final pre-ranking temporal-filter evaluation; do not present the superseded post-ranking result as final.
- The strict temporal rule is earlier decision year only because ILDC query dates are year-granular.
- The Week 13 review status is author_self_review_fallback; it cannot be generalized as an independent reviewer result.

## Retrieval mechanism behind the final recall figures

Source: `artifacts/retrieval_investigation_summary.md`. Three bounded changes preceded the final freeze; their mechanism and effect must accompany final recall figures in Results.

- **Round 1:** Replace legacy first-32-term query construction with deterministic TF-IDF salient terms from the full facts-only input. Removed opening procedural boilerplate without changing the BM25 architecture.
- **Round 2:** Repair the direct shared-phrase self-match guard by retaining the 100 shared-six-token floor and requiring 80% unique source-phrase coverage. Recovered three additional authorities in the corrected development probe and withdrew the prior broad lexical-mismatch claim.
- **Round 3:** Apply the strict earlier-year temporal rule to the BM25 candidate relation before ranking and the top-100 cutoff. Improved held-out Recall@5 from 5/30 to 12/30, Recall@100 from 12/30 to 15/30, and selected expected authorities from 11/30 to 12/30, without losing any original retrieval successes.

## Indexed qualitative findings

- **Boilerplate-uncertainty miscalibration** — Source: `artifacts/week13_review_summary.md (Case 2013_35)`. The identical generic uncertainty language was visually clear but did not adapt to the high coherence of 2013_35's evidence; it signalled the same caution level as noisier evidence sets. This is a system-level limitation, not a format-specific result.
- **Eligible-pool size and lexical relevance are independent contributors** — Source: `artifacts/retrieval_investigation_summary.md`. 2013_35 remained absent despite 79 eligible candidates in its former raw top-100, while 1980_105 was recovered despite only three eligible raw candidates and became a top-5 hit after the final filter. This indicates residual lexical/relevance or ranking limitations beyond temporal filtering alone.

## Answer-key era distribution

Source: `artifacts/week11_temporal_prerank_evaluation.json`. The corrected 30-case answer-key subset contains 13/30 cases from the 1980s, so this era is overrepresented in the evaluated authority-recovery sample.

| Query-case decade | Cases |
|---|---:|
| 1970s | 5 |
| 1980s | 13 |
| 1990s | 9 |
| 2000s | 2 |
| 2010s | 1 |

## Explicit consistency checks

- **Self-review case alignment:** PASS. All seven Week 13 sample cases occur in the final 30-case answer-key analysis with the expected retrieval-outcome bucket, five passed displayed citation checks, and exact format-pair citation parity.
- **Population separation:** PASS. Outcome prediction is n=1,503, citation/grounding is n=30, and explanation-format review is n=7; no inventory row merges these populations.
