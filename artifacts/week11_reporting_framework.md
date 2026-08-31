# Week 11 Revised Reporting Framework

## Temporal exposure and control metrics

| Metric | Numerator | Denominator | Value |
|---|---:|---:|---:|
| FEER: future-ineligible retrieved candidates / all retrieved candidates | 1712 | 2743 | 0.624134 |
| FCER: future-ineligible final cited items / all final cited items | 0 | 135 | 0.000000 |

The FEER numerator counts only `ineligible` later-year candidates. The 267 same-year candidates are retained as an explicitly ambiguous/excluded bucket rather than silently treated as future evidence. FCER is zero because final evidence selection admits only temporally eligible candidates.

## E4-E3 prediction delta

Prediction Delta (E4 - E3): **not defined**. Neither frozen system emits an outcome-prediction label, so a numeric prediction delta would be fabricated. E4 adds verification to E3's evidence presentation; it is not a second outcome classifier.

## Operational definitions

| Term | Implemented project definition |
|---|---|
| Temporal existence | An eCourts item has a parseable exact `decision_date`; candidates missing this metadata are excluded. ILDC query dates are available only at year granularity. |
| Temporal effectiveness | The strict filter prevents later-year material from final citations: measured by FCER. Later-year material can remain visible in the candidate log, measured by FEER, for auditability. |
| Temporal applicability | For an ILDC query with year Y, an eCourts precedent is eligible only when `precedent_decision_year < Y`. Same-year items are logged as `ambiguous_excluded`; later-year items are `ineligible`. |
| Provenance validity | Each displayed evidence item must reproduce a corpus chunk's stable source ID, citation, decision date, court, PDF/page/character locator, exact passage text, and retrieval-run membership. |
| Authority consistency | A final displayed authority matches the independently verified answer-key authority by stable source ID, normalized citation, or normalized title plus exact decision date. |
| Future evidence exposure | FEER: the share of logged, post-duplicate-exclusion retrieval candidates that are later-year and therefore ineligible. It is distinct from FCER, which measures whether future evidence reached final cited output. |
