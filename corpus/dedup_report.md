# ILDC / eCourts Deduplication and Leakage Report

## Method

- Exact match: canonicalized eCourts `case_id` values of the form `YYYY INSC N` were compared with ILDC IDs of the form `YYYY_N`.
- Near match: for records without an exact ID match, eCourts title/petitioner/respondent tokens were compared only with ILDC text from the same year. A near match requires at least two shared distinctive terms and 80% title/party-token coverage. This is a conservative audit and does not claim to identify every duplicate.

## Results

- ILDC cases inspected: 7,593
- eCourts metadata rows downloaded: 39,073
- Distinct eCourts case IDs inspected: 33,700
- Exact canonical-ID overlaps (unique ILDC cases): 5,391
- High-confidence near title/party overlaps (unique ILDC cases): 261
- Unique ILDC cases flagged for exclusion review: 5,652
- Unique ILDC/eCourts candidate pairs flagged: 5,710

## Overlaps by fixed ILDC split

| ILDC split | Exact pairs | High-confidence near pairs | Unique matching eCourts cases |
| --- | ---: | ---: | ---: |
| Train | 3,632 | 234 | 3,786 |
| Validation | 702 | 26 | 726 |
| Test | 1,057 | 59 | 1,111 |

## Retrieval-time handling rule

The eCourts document is retained in the corpus for unrelated queries. For an ILDC query, retrieval excludes every candidate paired with that query in `dedup_matches.csv` (either exact canonical-ID or high-confidence title/party match). This query-specific rule prevents a system from retrieving the target judgment itself while preserving legitimate precedent for other cases. The near-match threshold is: same year, at least two shared distinctive title/party terms, and at least 80% coverage of the eCourts title/party-token set in ILDC text.

Flagged cases are recorded in `dedup_matches.csv` (local-only corpus output). Any flagged record must be excluded from that query case's retrieval candidates in E3/E4.
