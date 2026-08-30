# E2 Corrected Chunk-and-Pool Training Audit

The evaluated checkpoint is `artifacts\e2_chunk_pool_checkpoints_cached\checkpoint-6318`. It matches the saved result record: `False`.

## Validation curve

| Epoch | Mean-logit accuracy | Mean-logit macro F1 | Majority-vote accuracy | Loss |
| ---: | ---: | ---: | ---: | ---: |
| 1.00 | 0.5381 | 0.4481 | 0.5371 | 0.7560 |
| 2.00 | 0.6063 | 0.5989 | 0.6002 | 0.8095 |
| 3.00 | 0.6124 | 0.6067 | 0.5951 | 1.0740 |

Best validation mean-logit accuracy: `0.612411` at the final saved checkpoint.
Test coverage: `1503/1503` documents (100.00%); no input is silently truncated to a prefix.
Primary test confusion matrix (rows=true, columns=predicted; labels 0/1): `[[527, 222], [384, 370]]`.
