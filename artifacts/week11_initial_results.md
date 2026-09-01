# Week 11 Final Quantitative Evaluation

## Frozen evaluation scopes

| Metric family | Population | n |
|---|---|---:|
| E1/E2 outcome prediction | Eligible cases in the full frozen ILDC test split | 1,503 |
| E3/E4 retrieval, citation, grounding, provenance, and temporal integrity | Source-verified, corrected-alignment-gated answer-key subset of the fixed ILDC test split | 30 |

The reference-evidence set is frozen at 30 cases for this evaluation round. The originally planned 40 cases were an aspirational coverage target, not an evaluation gate; the remaining 10 are deferred to the post-Week-11 backlog. The frozen evaluation record is `config/week11_evaluation_round.json`, based on commit `f6ea888d8a56352114d7ca7a672a7094854eb84c`.

## Results

| Experiment / metric family | n | Accuracy | Macro F1 | Recall@5 | Recall@100 | Authority P/R/F1 | Citation groundedness | Provenance validity | Temporal violation | Unsupported claims |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| E1, TF-IDF + Logistic Regression outcome prediction | 1,503 | 0.613440 | 0.612342 | -- | -- | -- | -- | -- | -- | -- |
| E2, InLegalBERT chunk-and-pool (mean logits, primary) outcome prediction | 1,503 | 0.596806 | 0.592358 | -- | -- | -- | -- | -- | -- | -- |
| E2, InLegalBERT chunk-and-pool (majority vote, secondary) outcome prediction | 1,503 | 0.601464 | 0.593682 | -- | -- | -- | -- | -- | -- | -- |
| E3, final pre-ranking temporal retrieval + controlled evidence-grounded answer | 30 | N/A | N/A | 0.400000 | 0.500000 | 0.080000 / 0.400000 / 0.133333 | 1.000000 | 1.000000 | 0.000000 | 0.000000 |
| E4, E3 plus citation/provenance/temporal verification | 30 | N/A | N/A | 0.400000 | 0.500000 | 0.080000 / 0.400000 / 0.133333 | 1.000000 | 1.000000 | 0.000000 | 0.000000 |

E3/E4 do not output an outcome label, so outcome accuracy is not fabricated for those systems. E3 and E4 share the frozen retrieval/selection output; E4 adds hard citation, provenance, and temporal verification. The final answer-key metrics have 30 expected authorities, 150 selected evidence items, and 150 displayed citation checks. The full machine-readable final record is `artifacts/week11_temporal_prerank_evaluation.json`; `artifacts/week11_initial_evaluation.json` is retained as the superseded post-ranking-filter baseline.

### Temporal reporting metrics

| Metric | Numerator / denominator | Value |
|---|---|---:|
| FEER (future-ineligible retrieved candidates / all retrieved candidates) | 0 / 3,000 | 0.000000 |
| FCER (future-ineligible final cited output / all final cited output) | 0 / 150 | 0.000000 |

The final configuration applies strict earlier-year filtering before BM25 ranking and the top-100 cutoff, so every returned candidate is eligible. The preserved post-ranking baseline had FEER 1,712/2,743 = 0.624134 plus 267 same-year ambiguous candidates; this dilution motivated the bounded test. FCER confirms that no later-year item reached the final cited output in either configuration.

**Prediction Delta (E4 - E3): not defined.** The frozen E3/E4 systems do not emit outcome-prediction labels, so there is no numeric prediction delta to report without fabrication. The full temporal definitions and counts are in `artifacts/week11_reporting_framework.md`.

## Configuration provenance and precision definition

The final E3/E4 run used `week11-bm25-salient-terms-preranked-temporal-v3`: `tfidf-segment-salient-terms-v1` query construction, candidate depth 100, five-source diverse selection, strict earlier-year filtering before BM25 ranking, and the coverage-qualified direct self-match guard. It did not use the superseded raw self-match rule, legacy first-32-term builder, pre-correction ID mapping, or post-ranking temporal filtering. E2 is the corrected 512-token, 50-token-overlap chunk-and-pool model; the former 256-token result remains discarded and is not used here.

Authority-consistent precision is **12 expected-authority evidence items / 150 final selected and displayed evidence items = 0.080000**. It is not precision over every raw top-100 candidate. Recall is 12/30 cases where the predefined authority was selected, and the resulting F1 is 0.133333. This implements the frozen metric's intended question: whether the citations actually displayed by the system match the predefined reference evidence.

The observed precision should be read against its structural ceiling. Each query has one predefined reference authority while the frozen renderer displayed 150 citations across 30 cases, or **5 citations per case**. Even a selector that displayed the expected authority for every query, while retaining that fixed number of citations, could achieve at most **1 / 5 = 0.200000** authority-consistent precision (30/150). The observed 0.080000 is therefore 40.0% of that fixed-cardinality ceiling; it is not directly comparable to a single-citation-per-case precision score.

## Evaluation-round finality

Both result families are final for this evaluation round: E1/E2 outcome metrics remain final at n=1,503, and E3/E4 evidence metrics remain final at n=30. The deferred ten answer-key cases neither require nor justify rerunning E1/E2. If they are verified later, their E3/E4 metrics will be reported as a clearly separate answer-key extension/evaluation round; they will not overwrite the frozen n=30 Week 11 results.

## Answer-key sanity check

All 30 frozen cases are fixed-test-split members and pass the current, corrected content-alignment gate. Twenty are in the 1958--1993 identifier-collision-risk era; every one passed individually. See `artifacts/week11_answer_key_sanity_check.json`.
