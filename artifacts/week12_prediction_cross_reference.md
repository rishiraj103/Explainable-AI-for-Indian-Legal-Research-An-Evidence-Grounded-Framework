# Week 12 Prediction and Evidence Cross-Reference

## Verified prediction reproduction

E1 was deterministically reconstructed from the frozen C=10.0 configuration and reproduced 0.613440 accuracy / 0.612342 macro F1 exactly. E2 was inferred from frozen checkpoint `checkpoint-6318` on its cached 512-token windows and reproduced 0.596806 / 0.592358 exactly for mean-logit pooling.

## E1/E2 outcome disagreement

| Population | Both correct | E1 correct, E2 wrong | E1 wrong, E2 correct | Both wrong |
|---|---:|---:|---:|---:|
| Full test, n=1,503 | 684 | 238 (`1957_125`) | 213 (`1967_145`) | 368 |
| Answer-key cohort, n=30 | 18 | 3 (`1997_792`) | 3 (`1995_375`) | 6 |

## Mandatory E3/E4 categories

| Category | Result |
|---|---|
| E2 wrong, E3/E4 outcome correct | Structurally inapplicable: E3/E4 do not predict an outcome. None of the three E2-wrong cohort cases also retrieved and selected the expected authority. |
| E3 correct, E4 wrong | 0/30 on the applicable verification interpretation: all 135 E3-displayed citations pass E4 verification. |
| E3/E4 outcome correct but citation unsupported | Structurally inapplicable: no E3/E4 outcome label; unsupported citations 0/135. |
| Correct authority retrieved but final answer wrong | Structurally inapplicable: the controlled brief has no adjudicated final-outcome claim. |
| Citation traceable but authority-consistency fails | 18/30 cases; example `1997_792`. These citations are traceable, but the expected authority was not selected. |
| Citation later than the query case | 0/30 cases and 0/135 citations. |
| Explanation faithfulness spot check | 5/5 pass: `2008_1629`, `1997_792`, `1980_133`, `2002_944`, `1988_96`. Each displayed evidence reference maps exactly to a persisted retrieved chunk; no unsupported highlight was detected. |
