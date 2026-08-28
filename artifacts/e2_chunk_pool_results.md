# E2 corrected InLegalBERT chunk-and-pool baseline

Model: `law-ai/InLegalBERT` at revision `b5ecfed8ed6cf9d25a3cb8225a8c52f161f7401a`. Facts extractor: `ildc-predecision-facts-v1`. Retrieval/evidence lookup: **not used**.
Each document was tokenized into `512`-token overflow windows with `50`-token overlap. The selected checkpoint was chosen by validation document-level mean-logit accuracy.

## Complete input coverage

| Split | Eligible documents | Windows | Median windows/document | Documents fully represented |
| --- | ---: | ---: | ---: | ---: |
| train | 5020 | 33702 | 5 | 100.00% |
| validation | 983 | 6054 | 5 | 100.00% |
| test | 1503 | 9576 | 5 | 100.00% |

All `1503` eligible test documents are represented by at least one overflow window; no facts-only input is cut to a single 256-token prefix.

## Final locked test evaluation

| Pooling method | Accuracy | Macro F1 | Class 0 F1 | Class 1 F1 |
| --- | ---: | ---: | ---: | ---: |
| Mean logits (primary) | 0.5968 | 0.5924 | 0.6349 | 0.5498 |
| Majority vote (comparison) | 0.6015 | 0.5937 | 0.6499 | 0.5375 |

Primary confusion matrix (rows=true, columns=predicted; labels 0,1): `[[527, 222], [384, 370]]`.
