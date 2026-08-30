# Week 11 Initial Quantitative Evaluation

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
| E3, frozen retrieval + controlled evidence-grounded answer | 30 | N/A | N/A | 0.166667 | 0.400000 | 0.081481 / 0.366667 / 0.133333 | 1.000000 | 1.000000 | 0.000000 | 0.000000 |
| E4, E3 plus citation/provenance/temporal verification | 30 | N/A | N/A | 0.166667 | 0.400000 | 0.081481 / 0.366667 / 0.133333 | 1.000000 | 1.000000 | 0.000000 | 0.000000 |

E3/E4 do not output an outcome label, so outcome accuracy is not fabricated for those systems. E3 and E4 share the frozen retrieval/selection output; E4 adds hard citation, provenance, and temporal verification. The answer-key metrics have 30 expected authorities, 135 selected evidence items, and 135 displayed citation checks. The full machine-readable per-case record is `artifacts/week11_initial_evaluation.json`.

## Answer-key sanity check

All 30 frozen cases are fixed-test-split members and pass the current, corrected content-alignment gate. Twenty are in the 1958--1993 identifier-collision-risk era; every one passed individually. See `artifacts/week11_answer_key_sanity_check.json`.
