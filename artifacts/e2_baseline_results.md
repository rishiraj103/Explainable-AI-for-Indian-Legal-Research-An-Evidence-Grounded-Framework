# E2 InLegalBERT facts-only baseline

Model: `law-ai/InLegalBERT` at revision `b5ecfed8ed6cf9d25a3cb8225a8c52f161f7401a`  
Facts extractor: `ildc-predecision-facts-v1`; retrieval/evidence lookup: **not used**.  
Best checkpoint was selected by validation accuracy: `artifacts/e2_training_checkpoints/checkpoint-939`.

## Fixed split accounting

| Split | Source rows | Eligible facts-only rows | Excluded rows | Eligible-ID SHA-256 |
| --- | ---: | ---: | ---: | --- |
| train | 5082 | 5020 | 62 | `d57f5865694547a83ba4adc8b03f65cc7a3ee8d98b2676b5726dcee24d830ce4` |
| validation | 994 | 983 | 11 | `4e53bd457b937d43bf185168c9f4b945e75b8a5d8be90fd583a7d4517932b0f0` |
| test | 1517 | 1503 | 14 | `afc0a58e0bbaa3d647f65877ee1b83933d53b4769d5cd2988b8301b596479c4d` |

## Final test result

- Accuracy: **0.5695**
- Macro F1: **0.5575**
- Class 0 F1: `0.6305`; Class 1 F1: `0.4845`.
- Confusion matrix (rows=true, columns=predicted; labels 0,1): `[[552, 197], [450, 304]]`.

## Comparison constraint

E1 and E2 use the identical frozen facts-extraction function and eligible IDs. E2 tokenizes those inputs to a 256-token maximum because of the model architecture and 4 GB GPU limit; this truncation is recorded and should be considered when attributing any E1/E2 difference solely to model architecture.
