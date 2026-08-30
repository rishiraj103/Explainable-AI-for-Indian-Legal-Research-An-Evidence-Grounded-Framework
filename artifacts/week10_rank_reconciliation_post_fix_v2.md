# Week 10 Rank-Discrepancy Reconciliation

| Case | Historical short issue-query rank | Current same-query legacy rank | Source present / retained | Explanation |
| --- | ---: | ---: | --- | --- |
| `2008_1629` | 29 | 29 | `True` | short manual issue query versus full facts-only regression input |
| `1995_425` | 56 | 56 | `True` | short manual issue query versus full facts-only regression input |
| `2002_944` | 75 | 75 | `True` | short manual issue query versus full facts-only regression input |

All three expected authorities remain present, temporally eligible, and retained by the corrected target/near-duplicate and content-self-match safeguards. Their historical ranks reproduce when the same short manually authored issue queries are used. The apparent discrepancy comes from comparing those issue-query ranks with the final regression's different full facts-only input, not from a corpus removal, an index change, or a false-positive duplicate exclusion.
