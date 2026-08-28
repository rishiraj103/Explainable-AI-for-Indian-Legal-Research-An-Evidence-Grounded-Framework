# E1 TF-IDF + Logistic Regression baseline

Configuration: `config\e1_baseline.json` (SHA-256 `ce52fe6601c92a9c9cb40a83bc6c0124c929070cbf5d64029b5e3b02ca47b55a`)  
Facts extractor: `ildc-predecision-facts-v1`  
Test evaluation was run only after validation selected the locked hyperparameter.

## Fixed split accounting

| Split | Source rows | Eligible facts-only rows | Excluded low-retention/short rows | Eligible-ID SHA-256 |
| --- | ---: | ---: | ---: | --- |
| train | 5082 | 5020 | 62 | `d57f5865694547a83ba4adc8b03f65cc7a3ee8d98b2676b5726dcee24d830ce4` |
| validation | 994 | 983 | 11 | `4e53bd457b937d43bf185168c9f4b945e75b8a5d8be90fd583a7d4517932b0f0` |
| test | 1517 | 1503 | 14 | `afc0a58e0bbaa3d647f65877ee1b83933d53b4769d5cd2988b8301b596479c4d` |

## Validation selection

| C | Accuracy | Macro F1 |
| ---: | ---: | ---: |
| 0.1 | 0.4995 | 0.3331 |
| 1.0 | 0.5565 | 0.4790 |
| 10.0 | 0.6134 | 0.5883 |

Selected `C=10.0` by validation accuracy; ties use the smaller C.

## Final test result

- Accuracy: **0.6134**
- Macro F1: **0.6123**
- Class 0 F1: `0.6330`; Class 1 F1: `0.5917`.
- Confusion matrix (rows=true, columns=predicted; labels 0,1): `[[501, 248], [333, 421]]`.
- Majority-class baseline: label `1` at `0.5017` accuracy; E1 improves accuracy by `11.18` percentage points.

## Reproducibility and limitation

The exact raw split-file and eligible-ID digests, package versions, seed, and all model settings are in the companion JSON. ILDC lacks gold-standard facts/reasoning boundaries; this frozen heuristic is a reproducible approximation and may retain legal reasoning or exclude material near a boundary.
