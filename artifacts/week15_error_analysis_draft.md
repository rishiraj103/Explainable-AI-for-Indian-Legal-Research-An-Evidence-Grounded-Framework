# Error Analysis

## Analysis protocol

The error analysis is a read-only examination of the final Week 11 artifacts under `week11-bm25-salient-terms-preranked-temporal-v3`. No model was retrained, no inference or retrieval was rerun, and no configuration or answer-key entry was changed in response to test outcomes. Outcome-prediction errors are analyzed on the 1,503-case E1/E2 population; retrieval and verification errors are analyzed separately on the 30-case answer-key subset.

## Outcome-model disagreement

Reconstructed E1 predictions and inference-only E2 predictions exactly reproduced their frozen aggregate metrics before the per-case vectors were joined. Across 1,503 cases, both models were correct on 684 and both were wrong on 368; E1 alone was correct on 238, while E2 alone was correct on 213. In the 30-case answer-key subset, both were correct on 18, E1 alone on three, E2 alone on three, and both were wrong on six. These disagreements show that the models are not identical despite E1's aggregate advantage, but they do not permit an outcome comparison with E3/E4, which do not produce outcome labels.

| Population | Both correct | E1 only correct | E2 only correct | Both wrong |
|---|---:|---:|---:|---:|
| Full fixed-test population | 684/1,503 | 238/1,503 | 213/1,503 | 368/1,503 |
| Answer-key subset | 18/30 | 3/30 | 3/30 | 6/30 |

## Exhaustive authority-recovery buckets

Expected-authority outcomes partition the 30 answer-key cases exhaustively. Twelve expected authorities were retrieved and selected, three were retrieved within the top 100 but omitted from the five-source display, and 15 were absent at k=100.

| Retrieval outcome | Count | Cases |
|---|---:|---|
| Retrieved and selected | 12/30 | `2008_1629`, `1995_322`, `1995_375`, `1986_176`, `1977_99`, `1981_187`, `1980_222`, `1980_105`, `1995_425`, `2002_944`, `1982_29`, `1988_96` |
| Retrieved but not selected | 3/30 | `1980_133` (rank 15), `1981_55` (rank 28), `1985_40` (rank 78) |
| Absent at k=100 | 15/30 | `1997_792`, `1993_185`, `1971_295`, `1974_36`, `1986_378`, `1984_136`, `2013_35`, `1980_217`, `1978_33`, `1977_145`, `1995_412`, `1995_403`, `1986_397`, `1994_632`, `1992_84` |

The three middle-bucket cases isolate selection from retrieval failure: the expected authority was available to the pipeline but ranked outside the five displayed sources. `1980_133` improved from rank 48 in the superseded post-ranking baseline to rank 15 under the final filter, yet still remained outside the display. The 15 absent cases instead require improvement before selection, through query construction, lexical matching, ranking, or corpus coverage.

## Verification errors versus authority-consistency errors

No displayed evidence item failed E4 verification: all 150 citations reproduced persisted passages and provenance, belonged to the relevant retrieval run, passed duplicate controls, and satisfied the strict earlier-year rule. No unsupported material claim was detected. On the applicable E3-to-E4 verification interpretation, there were therefore 0/30 cases in which E3 displayed evidence that E4 rejected.

Authority consistency presents a different error surface. In 18/30 cases, the single expected authority was not selected, even though every displayed citation was traceable. This includes both the three retrieved-but-unselected cases and the 15 absent-at-k=100 cases. The 138 displayed citations that differed from the key remain unlabelled for substantive relevance, so this count is evidence of reference-authority mismatch, not proof that the alternatives are legally wrong.

## Temporal and explanation-faithfulness checks

The final candidate relation returned 3,000/3,000 temporally eligible items, and all 150 final citations were eligible; later-year citation failures were therefore zero. Same-year items were excluded as ambiguous under the year-only policy. In the fixed five-case explanation-faithfulness spot check, every displayed evidence reference mapped to an exact persisted retrieved chunk, and no unsupported highlight was found.

## Failure interpretation

The dominant residual failure is expected-authority recovery, not verification after evidence is selected. The contrast between `2013_35` and `1980_105` shows why this cannot be assigned to temporal filtering alone: the former remained absent despite a large eligible pool in the earlier ordering, while the latter was recovered from a very small eligible pool and moved into the top five after pre-ranking. The remaining error surface therefore combines case-specific lexical mismatch, authority ranking, the five-source selection cutoff, and possible corpus coverage. The evaluation does not disentangle these contributors causally.

## Draft provenance

This section is adapted from the final `artifacts/week12_error_analysis.md`, with outcome-disagreement counts from `artifacts/week12_prediction_cross_reference.md` and final citation cardinalities from `artifacts/week14_results_evidence_inventory.json`.
