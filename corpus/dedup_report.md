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

Flagged cases are recorded in `dedup_matches.csv` (local-only corpus output). Any flagged record must be excluded from that query case's retrieval candidates in E3/E4.
