# Week 11 Mandatory Error Analysis

## Headline

**Verification succeeds for retrieved evidence; recovery of the predefined authority is the binding constraint.** All 135 displayed citations passed grounding and provenance checks, with zero temporal violations and zero unsupported-claim detections. Retrieval found the expected authority for 12/30 cases at k=100 and selected it for 11/30.

## Mandatory retrieval buckets

| Bucket | Cases | Case IDs |
|---|---:|---|
| Correct authority retrieved and selected | 11 | `2008_1629`, `1995_322`, `1995_375`, `1986_176`, `1977_99`, `1980_222`, `1980_105`, `1995_425`, `2002_944`, `1982_29`, `1988_96` |
| Correct authority retrieved but not selected | 1 | `1980_133` (best rank 48) |
| Correct authority absent at k=100 | 18 | `1997_792`, `1993_185`, `1971_295`, `1974_36`, `1986_378`, `1984_136`, `2013_35`, `1980_217`, `1978_33`, `1981_187`, `1977_145`, `1981_55`, `1995_412`, `1995_403`, `1986_397`, `1994_632`, `1985_40`, `1992_84` |

Recall@5 is 5/30 (0.166667). Some expected authorities were selected from ranks beyond five because selection is source-diverse and operates over the frozen top-100 candidate set; selected-support success is therefore 11/30, not limited to the Recall@5 count.

## Provenance-valid citations that are not the predefined authority

Of 135 displayed, provenance-valid citations, 124 are not the single predefined authority for their query; 19/30 cases do not display that expected authority. This is an **answer-key consistency** finding, not a substantive-irrelevance label: the answer key has one verified reference authority per case and does not provide a gold human relevance label for every alternative cited authority. No claim that any of these 124 citations is substantively irrelevant is made without such a label.

## Measurement provenance

This analysis reads the persisted run UUIDs from the initial Week 11 evaluation. It does not rerun retrieval or alter the index, query builder, answer key, or frozen configuration. It also corrects only a per-case presentation field: the original `expected_authority_retrieved_not_selected` value was computed before selection. Aggregate Week 11 metrics were unaffected.
