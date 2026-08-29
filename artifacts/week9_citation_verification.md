# Week 9 citation and evidence verification

## Verification contract

Every authority rendered by E3 must be accepted by all of the following checks:

1. The linked chunk exists in the rebuilt eCourts corpus and each displayed provenance field is identical to the stored record.
2. The evidence passage is byte-for-byte the stored chunk text, so altered or invented passage text cannot inherit a real citation.
3. The chunk was recorded in the PostgreSQL `retrieval_results` rows for this exact query run.
4. The authority is not the query case itself and is not an audit-listed near duplicate.
5. The authority decision year is strictly earlier than the ILDC query year. Same-year and later authorities fail, rather than being silently ignored.

The verifier also compares only successfully verified displayed authorities with the frozen source-first answer key. It reports a missing expected authority separately from an unverified or wrong displayed citation.

## Deterministic hand-authored tests

`tests/test_citation_verifier.py` contains 13 cases and all pass. The suite covers a valid citation; missing-corpus, altered-passage, altered-citation, non-retrieved, later-year, same-year, exact-query-duplicate, and near-duplicate failures; an authority without an evidence link; expected-authority match and miss accounting; and the no-evidence outcome.

## Live E3 provenance check

Run `8ec4fdc9-809d-4b40-940d-4c2c7fb369b6` queried fixed-test case `2008_1629` (year 2008) with the pay-scale/resignation issue query. The controlled E3 renderer selected five authorities. The verifier accepted all five: each was present in the corpus, unchanged, recorded in this retrieval run, non-duplicate, and dated before 2008. The machine-readable record is `artifacts/week9_real_e3_citation_verification.json`.

The answer key expects `(2006) 9 SCC 630` for this query. It was not among the five retrieved authorities. This is recorded as an **expected authority not retrieved**, while `wrong_or_unverified_displayed_citations` remains empty. This is an authority-recall finding, not a citation-grounding failure.

## Status

The citation/evidence verification module is working and remains separate from Week 10 explanation and freeze work. The answer-key population is still at 20/40 evaluation cases; the remaining Week 9 pacing work is tracked separately in the local checklist.
