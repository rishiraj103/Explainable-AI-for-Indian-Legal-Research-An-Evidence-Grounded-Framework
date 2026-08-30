# Identifier-Namespace Collision: Safety and Crosswalk Checkpoint

**Checkpoint status:** Steps A-C complete. Do not start answer-key
re-resolution, dev-probe rebuilding, or Week 10 freeze from this checkpoint.

## A. Retrieval-time self-leakage safety

`exclude_query_duplicate()` now has two independent controls:

1. It excludes an eCourts document only when it appears in the
   alignment-gated crosswalk for the current ILDC query, rather than when its
   syntactically similar identifier happens to match.
2. It compares the query's full ILDC text with every retrieved source document
   using direct contiguous six-token phrase fingerprints. A source with at
   least 100 shared phrases is excluded even when no ID crosswalk mapping yet
   exists.

The guard runs before temporal eligibility in `evidence_pipeline.py`. Unit
tests cover a verbatim/near-verbatim unmapped self-match (excluded) and a
topically similar but distinct document (retained).

The corrected `1977_183` top-100 smoke run is recorded in
`artifacts/rebuild_target_exclusion_corrected.json`: it excluded **0** chunks.
The old two-chunk exclusion depended on the unsafe `1977_183` / `1977 INSC
183` syntactic collision. The new result is a correction of false assurance,
not evidence that the true source has been located; it was not in the sampled
retrieval candidates under this smoke query.

## B. Reconciling the crosswalk counts

The two headline groups are different units of analysis:

| Measure | Meaning | Result |
| --- | --- | ---: |
| Syntactic-ID scan | Unique ILDC cases for which an eCourts `YYYY INSC N` can be mechanically rendered as the same-looking `YYYY_N` string | 5,391 candidates; 11 accepted; 5,380 rejected |
| Alignment-gated crosswalk | Deduplicated ILDC/eCourts candidate *pairs* from the union of syntactic hints and same-year title/party fallback candidates | 1,304 accepted; 7,623 rejected |

The full scan includes title/party fallback candidates beyond pure identifier
equality. Counts cannot be added directly: the syntactic and title/party
headline counts count unique ILDC cases, whereas the full scan counts candidate
pairs, and a case can have more than one candidate.

`corpus/dedup_matches.csv` now contains only the 1,304 accepted,
alignment-gated pairs and is the authoritative replacement for the former
5,710 unvalidated mapping file. Rejected candidates are retained separately in
`corpus/dedup_alignment_rejections.csv` for auditability.

## C. Downstream regeneration

- Regenerated `corpus/dedup_matches.csv` and
  `corpus/dedup_alignment_rejections.csv` from the corrected gate.
- Regenerated `corpus/dedup_report.md` and `corpus/temporal_overlap_audit.md`.
- Updated `corpus/dataset_manifest.md` with a standalone quantified
  namespace-collision section and replacement mapping counts.
- Confirmed all retrieval and citation command paths consume
  `corpus/dedup_matches.csv` through `query_exclusion_cases()` or their shared
  `--dedup-matches` default. No runtime consumer reads a retained legacy
  mapping file.

## Scope boundary

This checkpoint changes neither the answer-key entries nor retrieval ranking
configuration. The nine content-mismatch entries and unresolved `2013_121`
must be re-resolved using the gate, then the entire 30-case answer-key
population revalidated before any dev-only retrieval probe is rebuilt.
