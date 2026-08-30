# ILDC/eCourts matching root-cause analysis

**Status:** root cause confirmed and the crosswalk/retrieval stopgap corrected.
This document preserves the diagnosis. Answer-key re-resolution and dev-probe
rebuild remain deliberately blocked until the separately recorded correction
checkpoint is complete; see `artifacts/matching_correction_checkpoint.md`.

## Root cause

`scripts/build_corpus_reports.py` treated every syntactically matching pair of
identifiers as an exact identity match:

1. `ildc_id_from_ecourts_case_id()` converts eCourts `YYYY INSC N` to
   `YYYY_N`.
2. `write_dedup_report()` joins that value directly to ILDC `id` and labels the
   result `exact_canonical_id` with score `1.0`.
3. `find_near_matches()` then skips every ILDC ID already in that exact set.

The `N` suffix in ILDC is therefore being assumed to be the eCourts `INSC`
serial number without evidence that the identifiers belong to the same
namespace. The full content-alignment audit shows that this assumption is
false for a material subset of cases. The title/party fallback does not rescue
these pairs because it is never run for an apparent exact match.

## Evidence that this is not an off-by-one or 2013 scraping shift

The 2013 cluster is a visible consequence of the namespace collision, not a
single shifted index. For example:

| ILDC ID | ILDC judgment content | Incorrect syntactic eCourts match | Content-aligned eCourts discovery |
| --- | --- | --- | --- |
| `2013_121` | Defective Model Answer Key / Bihar Staff Selection Commission | `2013 INSC 121`, *M/S Bagai Construction* | `2013 INSC 161`, `2013_4_753_766`, *Rajesh Kumar & Ors. v. State of Bihar & Ors.* |
| `2010_721` | *D. Velusamy* maintenance dispute | `2010 INSC 721`, *Subrata Das* | Text fingerprint identifies *D. Velusamy* source text; the numerical IDs are unrelated. |
| `2003_78` | Temporary Lady Doctor's termination | `2003 INSC 78`, *K.T. Venatagiri* liquor-distribution dispute | The direct source-text check rejects the syntactic pair. |

For `2013_121`, the correct eCourts source is 40 serial positions away from the
syntactic match, which rules out a simple one-position or year-boundary offset.
The test-set audit likewise found mismatches in 2001, 2002, 2008, 2013, and
2017.

## Required correction sequence

1. Remove canonical-ID equality as an identity assertion. It may remain only
   as a candidate-generation hint.
2. Run title/party and direct content checks for *all* candidates, including
   syntactic-ID candidates.
3. Require a content-alignment gate before a mapping can drive leakage
   exclusion, query-source verification, answer-key entry creation, or a dev
   probe.
4. Re-resolve the nine content-mismatch answer-key cases; treat unresolved
   `2013_121` as a replacement candidate if no validated primary-source match
   can be established.
5. Revalidate every corrected/replaced entry before the dev probe is rebuilt.

## Timeline impact

This is a correction milestone, not routine Week 9/10 work. The Week 10
reproducibility freeze and all Week 11 metrics that depend on the answer key
remain blocked until the 30-entry answer-key population is again content
aligned (or transparently corrected/excluded), followed by a rebuilt dev-only
probe and bounded retrieval investigation. The schedule must not be compressed
by omitting those validation stages.
