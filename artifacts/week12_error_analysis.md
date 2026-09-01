# Week 12 Final Error Analysis

## Basis and scope

This final analysis is derived from the final pre-ranking temporal-filter Week 11 evaluation only. It is read-only: no model was retrained or inferred, no retrieval was rerun, and no answer-key or configuration setting changed.

## Central finding

**Verification succeeds for retrieved evidence; expected-authority recovery remains the binding limitation.** All 150 displayed citations passed grounding, provenance, and temporal checks, with zero unsupported claims. Expected-authority Recall@5 is 12/30 and Recall@100 is 15/30.

## Final retrieval buckets

| Bucket | Count | Cases |
|---|---:|---|
| Correct authority retrieved and selected | 12/30 | `2008_1629`, `1995_322`, `1995_375`, `1986_176`, `1977_99`, `1981_187`, `1980_222`, `1980_105`, `1995_425`, `2002_944`, `1982_29`, `1988_96` |
| Correct authority retrieved but not selected | 3/30 | `1980_133` (rank 15), `1981_55` (rank 28), `1985_40` (rank 78) |
| Correct authority absent at k=100 | 15/30 | `1997_792`, `1993_185`, `1971_295`, `1974_36`, `1986_378`, `1984_136`, `2013_35`, `1980_217`, `1978_33`, `1977_145`, `1995_412`, `1995_403`, `1986_397`, `1994_632`, `1992_84` |

`1980_133` remains retrieved-but-not-selected, but its best matching rank improved from 48 in the post-ranking baseline to 15 under the final pre-ranking filter. `1981_55` (rank 28) and `1985_40` (rank 78) are the two additional retrieved-but-not-selected cases.

## Final populated mandatory error-analysis table

| Frozen-plan category | Count / denominator | Example | Interpretation |
|---|---:|---|---|
| E2 wrong, E3/E4 correct | N/A | `2008_1629` | Structurally inapplicable: E3/E4 do not emit outcome labels. 3 E2-wrong cases retrieved and selected the expected authority, but that is evidence recovery rather than an outcome prediction. |
| E3 correct, E4 wrong | 0/30 | None | All 150 E3-displayed citations passed E4 verification. |
| E3/E4 prediction correct but citation unsupported | N/A | None | E3/E4 have no outcome labels; unsupported citations are 0/150. |
| Correct authority retrieved but final answer wrong | N/A | `2008_1629` | The controlled brief makes no adjudicated legal outcome claim, so final-answer correctness is not defined. |
| Citation traceable but authority-consistency fails | 18/30 cases | `1997_792` | Citations are provenance-valid but the predefined authority was not selected; this is not a substantive-irrelevance judgment. |
| Citation later than the historical case date | 0/30 cases; 0/150 citations | None | Confirmed per case and displayed citation. |
| Explanation highlights text not corresponding to retrieved evidence | 0/5 fixed spot checks | `2008_1629` | Every reconstructed highlight mapped to an exact persisted retrieved chunk. |

## Retrieval-investigation summary for Discussion and Limitations

Three bounded investigations were completed before the final freeze. First, the legacy first-32-term query construction was replaced with deterministic TF-IDF salient terms drawn from the full facts-only input; this removed opening procedural boilerplate from the query without changing the BM25 architecture. Second, the original direct shared-phrase self-match guard was found to suppress quoted earlier authorities. It was repaired by retaining the 100 shared-six-token floor but also requiring 80% unique source-phrase coverage; the corrected dev probe recovered three additional authorities and withdrew the earlier broad lexical-mismatch claim. Third, the post-ranking temporal filter was moved into the BM25 candidate relation before ranking and the top-100 cutoff. This final change improved held-out Recall@5 from 5/30 to 12/30, Recall@100 from 12/30 to 15/30, and selected expected authorities from 11/30 to 12/30, without losing any of the original 12 retrieval successes.

The remaining misses are not explained solely by temporal filtering. `2013_35` remained absent even though its former raw top-100 contained 79 eligible candidates, whereas `1980_105` was recovered despite only three eligible raw candidates in the earlier ordering and became a top-5 hit after the final filter. Together these contrasts indicate residual lexical/relevance mismatch or authority-ranking limitations rather than a remaining filtering artifact. The final system therefore demonstrates that provenance, grounding, and temporal controls can be perfect for displayed evidence while expected-authority coverage remains incomplete.

The E3-to-E4 comparison reflects a system-level intervention bundling provenance constraints, citation validation, structured explanation, and temporal integrity; it does not isolate the causal contribution of any single component.
