# Locked E1–E2 Comparison (Corrected E2)

Both experiments use `ildc-predecision-facts-v1`, the same eligible fixed ILDC split cases, and no retrieval/evidence lookup.

| Test metric | E1: TF-IDF + Logistic Regression | E2: InLegalBERT mean logits (primary) | E2: majority vote (comparison) |
| --- | ---: | ---: | ---: |
| Accuracy | 0.6134 | 0.5968 | 0.6015 |
| Macro F1 | 0.6123 | 0.5924 | 0.5937 |

Majority-class baseline accuracy: `0.5017`. Corrected E2 trails E1 by `1.66` percentage points (mean logits) and `1.20` points (majority vote).

## Discarded prior result

The old 256-token prefix E2 result (accuracy `0.5695`, macro F1 `0.5575`) is **discarded — truncation bug**: 1,491/1,503 eligible test inputs (99.20%) were truncated. It must not be compared with E1 as a final E2 result.

## Conclusion

Corrected InLegalBERT trails E1 under both pooling reports, while both exceed the 50.17% majority-class baseline. The discarded 256-token result is retained only for traceability.
