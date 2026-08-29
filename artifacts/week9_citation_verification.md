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

`tests/test_citation_verifier.py` contains 15 cases and all pass. The suite covers a valid citation; a fabricated case-name claim; missing-corpus, altered-passage, altered-citation, non-retrieved, later-year, same-year, exact-query-duplicate, and near-duplicate failures; an authority without an evidence link; expected-authority match and miss accounting; parallel-reporter reconciliation; and the no-evidence outcome. The later-year test asserts that temporal ineligibility is the only failure, isolating the temporal rule.

## Live E3 provenance check

Run `8ec4fdc9-809d-4b40-940d-4c2c7fb369b6` queried fixed-test case `2008_1629` (year 2008) with the pay-scale/resignation issue query. The controlled E3 renderer selected five authorities. The verifier accepted all five: each was present in the corpus, unchanged, recorded in this retrieval run, non-duplicate, and dated before 2008. The machine-readable record is `artifacts/week9_real_e3_citation_verification.json`.

The answer key expects `(2006) 9 SCC 630` for this query. The same authority is present in the eCourts corpus as `S_2006_2_582_600`, using its parallel citation `[2006] SUPP. 2 S.C.R. 582`, and was an eligible BM25 candidate at rank 29. It was therefore **retrieved but not selected** for the five-passage answer, not absent from the corpus. The answer-key comparison now reconciles a parallel reporter citation using normalized title plus exact decision date and reports this state separately. `wrong_or_unverified_displayed_citations` remains empty.

### Deferred Week 12 error-analysis candidate

Tag `2008_1629` / `S_2006_2_582_600` as a concrete **correct authority retrieved but not selected** instance. At Week 11–12, compare it with the other frozen answer-key queries to determine whether rank-29 omission is isolated or recurs because the Week 7 source-diverse selector favors other passages over a known authority. This is a recorded analysis question only; the frozen retrieval and selection configuration is unchanged.

## Status

The citation/evidence verification module is working and remains separate from Week 10 explanation and freeze work. The answer-key population is still at 20/40 evaluation cases; the remaining Week 9 pacing work is tracked separately in the local checklist.
