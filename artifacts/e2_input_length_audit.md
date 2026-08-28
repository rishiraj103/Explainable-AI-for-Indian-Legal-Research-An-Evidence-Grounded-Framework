# E2 facts-input token-length audit

Tokenizer: `law-ai/InLegalBERT` at revision `b5ecfed8ed6cf9d25a3cb8225a8c52f161f7401a`. Token counts exclude special tokens, so the actual encoded sequence is two tokens longer for the standard BERT pair markers.
InLegalBERT configuration supports `512` positions. The originally run E2 configuration used a `256`-token limit.

| Split | Eligible cases | Median | P90 | P95 | P99 | Max | >256 tokens | >512 tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 5020 | 2208 | 5260 | 7256 | 13535 | 65672 | 4999 (99.58%) | 4914 (97.89%) |
| Validation | 983 | 2020 | 4851 | 6633 | 11561 | 24731 | 977 (99.39%) | 949 (96.54%) |
| Test | 1503 | 2110 | 5148 | 6890 | 12550 | 31257 | 1491 (99.20%) | 1454 (96.74%) |

## Audit interpretation

On the locked test population, 1491 of 1503 inputs (99.20%) exceed the implemented 256-token limit; 1454 (96.74%) exceed 512 tokens. The 256-token cap is therefore an explicit implementation limitation to evaluate before accepting E2 as a model-only comparison.
