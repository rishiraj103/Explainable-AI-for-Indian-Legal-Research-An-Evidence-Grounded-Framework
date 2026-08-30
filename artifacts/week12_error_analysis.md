# Week 12 Error Analysis

## Basis and scope

This analysis uses the finalized Week 11 records only. It does not rerun a model, change retrieval, alter the answer key, or tune on test outcomes. E1/E2 outcome metrics are final at n=1,503; E3/E4 authority and integrity measures are final at n=30 for this evaluation round.

## Central finding

**Verification succeeds for retrieved evidence; expected-authority retrieval coverage is the binding limitation.** The frozen E4 verifier accepted all 135 displayed citations with zero temporal violations and zero unsupported-claim detections, while only 11/30 expected authorities were selected and 18/30 were absent at k=100.

## Mandatory categories

| Category | Result |
|---|---|
| E1 versus E2 | E1 accuracy/macro F1: 0.613440/0.612342; corrected E2 mean-logit: 0.596806/0.592358. E2 trails E1 by 0.016634 accuracy. Per-case prediction vectors were not retained, so no post-hoc disagreement example is fabricated. |
| Correct authority retrieved and selected | 11/30: `2008_1629`, `1995_322`, `1995_375`, `1986_176`, `1977_99`, `1980_222`, `1980_105`, `1995_425`, `2002_944`, `1982_29`, `1988_96`. |
| Correct authority retrieved but not selected | 1/30: `1980_133`, with its first matching chunk at rank 48. This is the concrete selection-stage miss. |
| Correct authority absent at k=100 | 18/30: `1997_792`, `1993_185`, `1971_295`, `1974_36`, `1986_378`, `1984_136`, `2013_35`, `1980_217`, `1978_33`, `1981_187`, `1977_145`, `1981_55`, `1995_412`, `1995_403`, `1986_397`, `1994_632`, `1985_40`, `1992_84`. |
| Provenance-valid but not answer-key authority | 124/135 displayed citations differ from the one reference authority per case. This is an answer-key-consistency finding, not evidence of substantive irrelevance without a human relevance label. |
| Temporal violations | 0/135. No violation example exists in the frozen evaluation. |
| E3/E4 outcome comparison | Not applicable: E3/E4 do not emit an outcome label. |

## Interpretation for results/discussion

The results distinguish two reliability properties. Once evidence is selected, the system reliably preserves provenance, grounding, and temporal eligibility. It does not reliably recover the single predefined authority within its candidate set, so high citation validity must not be presented as high authority coverage. The fixed five-source display policy also caps authority-consistent precision at 0.222222 with 4.5 displayed citations per case; observed precision is 0.081481 (36.7% of that ceiling).
