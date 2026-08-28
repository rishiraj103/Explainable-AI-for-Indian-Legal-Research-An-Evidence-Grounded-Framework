# Post-rebuild retrieval safety checks

Performed after the 2026-08-28 provenance and BM25 rebuild.

## Cross-corpus target-case exclusion

The existing cross-corpus audit still applies because the rebuild retained the
same eCourts case IDs, citations, and dedup-match file. To verify that the
rebuilt retrieval path actually uses it, an exact ILDC test overlap was run:

- ILDC query ID: `1977_183`
- Matched eCourts case: `1977 INSC 183` (`[1978] 1 S.C.R. 560`)
- Query text: `SARVESHWAR PRASAD SHARMA STATE OF MADHYA PRADESH`
- Candidate window: 100
- Result: `query_duplicate_chunks_excluded = 2`; three older, unrelated
  precedents were returned as evidence.

This confirms that query-time case-ID/citation deduplication remains active
after rebuilding PostgreSQL and BM25. The cross-corpus report retains the
split-level overlap counts and the documented rule in `corpus/dedup_report.md`.

## Elephant-corridor retrieval failure

The one 19/20 QA failure is not caused by the three residual OCR exclusions.
The relevant source remains present in the rebuilt corpus:

- `2020_10_273_298`, `2020 INSC 597`
- Decision date: 2020-10-14
- Subject: elephant corridor/environmental protection

All 30 lexical candidates for the fixed query were from 2020. Because the
query year is also 2020 and ILDC has year-only dates, the frozen temporal
policy labels them `ambiguous_excluded`; it returns no evidence rather than
risking post-decision leakage. This is a known year-granularity limitation,
not a loss caused by corpus repair.
