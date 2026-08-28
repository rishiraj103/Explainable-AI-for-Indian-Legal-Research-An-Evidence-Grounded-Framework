# E1 facts-extraction exclusion audit

The frozen facts-only gate excluded **87 / 7593 (1.15%)** ILDC rows before E1. This audit compares those rows with the retained E1 population; it does not change the frozen extraction rule or E1 result.

## Overall comparison

| Population | Rows | Label counts | Source words (P10 / median / P90) | Year range |
| --- | ---: | --- | --- | --- |
| Retained | 7506 | `{0: 4356, 1: 3150}` | `{'p10': 1285.5, 'median': 2949.5, 'p90': 7119.0}` | `[1947, 2019]` |
| Excluded | 87 | `{0: 43, 1: 44}` | `{'p10': 513.4, 'median': 3527.0, 'p90': 11473.0}` | `[1957, 2008]` |

## Exclusion causes

- Eligibility failure reasons: `{'below_minimum_facts_words': 37, 'below_minimum_retained_fraction': 78}`.
- Boundary reasons among excluded rows: `{'dispositive_cue': 74, 'positional_cap': 5, 'section_header': 8}`.

## Broad header-derived case-type mix

These are rough opening-header categories, not substantive legal classifications.

- Retained: `{'civil': 68.44, 'criminal': 16.89, 'original': 5.76, 'other_or_unclassified': 7.55, 'writ_or_constitutional': 1.36}`
- Excluded: `{'civil': 67.82, 'criminal': 13.79, 'original': 5.75, 'other_or_unclassified': 9.2, 'writ_or_constitutional': 3.45}`

## Finding

The exclusions are a small share of the corpus and are not simply unusually short judgments: their median source length is compared directly above. They are near-balanced by label. The header mix is broadly civil-dominant in both groups; small-category percentage differences are descriptive only because the excluded group has 87 rows. The reported E1 population and its exclusions remain explicit in the experiment record.
