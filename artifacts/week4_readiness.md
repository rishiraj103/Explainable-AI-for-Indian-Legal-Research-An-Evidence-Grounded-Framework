# Week 4 Search-System Checkpoint

## Verified components

- **Evidence corpus:** 2,036,945 canonical eCourts chunks in local PostgreSQL.
  Archive duplicates are deduplicated by stable chunk ID, so evidence is not
  double-counted.
- **Search:** a 2.08 GiB disk-backed SQLite FTS5 BM25 index,
  `fts5-bm25-unicode61-v1`, built from the canonical PostgreSQL catalog.
- **Provenance:** each chunk preserves its stable source ID, citation, decision
  date, PDF page, and character boundary; every retrieval candidate rank and
  temporal status is recorded in PostgreSQL.
- **Temporal safety:** strict earlier-year evidence eligibility is enforced.
  The smoke and QA runs logged 98 same-year candidates as
  `ambiguous_excluded`; none was returned as usable evidence.
- **Relevance review:** 20 realistic legal queries were reviewed. Nineteen
  produced 2–3 relevant eligible results. One elephant-corridor query correctly
  produced no usable evidence because its highest matches were same-year.
- **Verification:** local PostgreSQL container healthy; 16 automated tests pass.

## Checkpoint decision

The Week 4 search system is functioning and ready for the Week 5 prediction
baseline. No Week 5 model-training work has been started.
