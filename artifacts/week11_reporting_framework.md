# Week 11 Final Temporal Retrieval Reporting Framework

## Temporal exposure and control metrics

| Metric | Numerator | Denominator | Value |
|---|---:|---:|---:|
| FEER: future-ineligible retrieved candidates / all retrieved candidates | 0 | 3000 | 0.000000 |
| FCER: future-ineligible final cited items / all final cited items | 0 | 150 | 0.000000 |

The final configuration applies the strict earlier-year rule to the candidate relation before BM25 ranking and `LIMIT 100`. Consequently all 3,000 logged candidates are eligible, FEER is zero, and same-year/future documents do not consume the returned top-100 depth. In the preserved post-ranking baseline, FEER was 0.624134 (1712/2743) with 267 same-year items. FCER remains zero because final evidence selection admits only temporally eligible candidates.

## E4-E3 prediction delta

Prediction Delta (E4 - E3): **not defined**. Neither frozen system emits an outcome-prediction label, so a numeric prediction delta would be fabricated. E4 adds verification to E3's evidence presentation; it is not a second outcome classifier.

## Operational definitions

| Term | Implemented project definition |
|---|---|
| Temporal existence | An eCourts item has a parseable exact `decision_date`; candidates missing this metadata are excluded. ILDC query dates are available only at year granularity. |
| Temporal effectiveness | The strict filter constrains the BM25 candidate relation before ranking, preventing later/same-year material from consuming top-k capacity. FEER and FCER are both measured as zero in the final run. |
| Temporal applicability | For an ILDC query with year Y, an eCourts precedent is eligible only when `precedent_decision_year < Y`. Same-year and later-year items are excluded before BM25 ranking; missing dates are excluded. |
| Provenance validity | Each displayed evidence item must reproduce a corpus chunk's stable source ID, citation, decision date, court, PDF/page/character locator, exact passage text, and retrieval-run membership. |
| Authority consistency | A final displayed authority matches the independently verified answer-key authority by stable source ID, normalized citation, or normalized title plus exact decision date. |
| Future evidence exposure | FEER: the share of returned retrieval candidates that are later-year and therefore ineligible. It is distinct from FCER, which measures whether future evidence reached final cited output. Under final pre-ranking filtering FEER is zero by construction, while the preserved post-ranking baseline documents the former exposure. |
