# Locked E1–E2 comparison

Both experiments used the frozen `ildc-predecision-facts-v1` extractor and exactly the same eligible cases in every fixed ILDC split. Neither used retrieval or evidence lookup.

| Test metric | E1: TF-IDF + Logistic Regression | E2: InLegalBERT | E2 − E1 |
| --- | ---: | ---: | ---: |
| Accuracy | 0.6134 | 0.5695 | -0.0439 (-4.39 pp) |
| Macro F1 | 0.6123 | 0.5575 | -0.0549 |

## Result

E2 did **not** beat E1 under the frozen Week 6 settings. This is recorded as the outcome of the planned comparison, not tuned away. E1 remains the stronger facts-only baseline on this test evaluation.

## Interpretation constraint

The shared extractor and eligible-ID hashes make the included case population comparable. E2 nevertheless tokenizes inputs to 256 tokens for the InLegalBERT architecture and 4 GB GPU limit, while E1 consumes its full extracted text. That fixed input-length difference is a documented limitation when attributing the result only to model architecture.
