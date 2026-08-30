# Final Week 9 retrieval-freeze regression

This is the one permitted non-iterative real-answer-key regression. It uses
the same full frozen facts-only input, BM25 index, temporal eligibility,
alignment-gated exclusion, and runtime content self-match guard for both query
builders. The six fixed-test controls were selected before this comparison:
the two historically retrieved-and-selected controls and four historically
retrieved-but-not-selected controls. Historical ranks came from short manual
issue queries, so they identify the controls but are not numerically compared
with the fresh full-facts ranks below.

| Case | Historical category | Legacy k=100 / k=500 | Salient k=100 / k=500 | Result |
| --- | --- | --- | --- | --- |
| `1995_412` | selected (rank 22 with issue query) | absent / absent | absent / absent | no degradation |
| `1986_397` | selected (rank 2 with issue query) | absent / absent | absent / absent | no degradation |
| `2008_1629` | retrieved, not selected (29) | absent / absent | absent / absent | no degradation |
| `1995_425` | retrieved, not selected (56) | absent / absent | absent / absent | no degradation |
| `2002_944` | retrieved, not selected (75) | absent / absent | absent / absent | no degradation |
| `1988_96` | retrieved, not selected (96) | absent / absent | rank 13, selected / rank 13 | improved |

The salient query builder is non-worsening on all six pre-specified controls
and improves one. Together with its dev-probe improvement (0/9 to 3/9 at
k=100 and 4/9 at k=500), this satisfies the final regression rule even though
the original dev-only majority threshold was not reached.

## Closing freeze decision

Adopt `tfidf-segment-salient-terms-v1` as the frozen query-construction method
for `week10-bm25-salient-terms-v1`. The unchanged components are the existing
SQLite BM25 index, candidate depth 100, strict temporal eligibility,
alignment-gated/corpus-content duplicate exclusion, and five-source diverse
selection. No additional retrieval configuration test or query variant is
permitted after this artifact.

Machine-readable run IDs, constructed results, and the mechanical adoption
flag are in `artifacts/week9_final_freeze_regression.json`.
