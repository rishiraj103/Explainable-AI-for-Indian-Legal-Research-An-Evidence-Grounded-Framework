# ILDC / eCourts Deduplication and Leakage Report

## Method

- Canonicalized ID equality is a candidate hint only, never an identity match.
- Every syntactic-ID or title/party candidate is accepted only after title/party and direct six-token content alignment both pass.

## Results

- ILDC cases inspected: 7,593
- eCourts metadata rows downloaded: 39,073
- Distinct eCourts case IDs inspected: 33,892
- Syntactic-ID candidates (unique ILDC cases): 5,391
- Title/party candidates (unique ILDC cases): 2,474
- Alignment-gated mappings accepted: 1,304
- Alignment-gated candidates rejected: 7,623
- Unique ILDC cases flagged for exclusion review: 1,262
- Unique ILDC/eCourts candidate pairs flagged: 1,304

Flagged cases are recorded in `dedup_matches.csv` (local-only corpus output). Any flagged record must be excluded from that query case's retrieval candidates in E3/E4.
