# Dataset Manifest

## ILDC Single — E1/E2 prediction baseline

- **Source:** [Exploration-Lab/IL-TUR](https://huggingface.co/datasets/Exploration-Lab/IL-TUR), CJPE `single_*` Parquet files.
- **License:** CC-BY-NC, as stated by the original CJPE repository; attribution is required and commercial use is prohibited.
- **Subset loaded:** ILDC Single, 7,593 cases: 5,082 train, 994 validation, and 1,517 test. The local validation split is the provided 2,511-row development pool with the 1,517 test IDs removed, yielding the original 994 validation cases.
- **Observed year range:** 1947–2019, derived from the `id` prefix only.
- **Fields used:** `id`, `text`, `label`, and the fixed local split assignment. Labels are binary: rejected (0) or accepted (1).
- **Known limitations:** ILDC has no exact decision date, citation, authority metadata, or document-level provenance fields. Its year-only ID is insufficient to order same-year precedents; all same-year eCourts precedents are therefore ambiguous and excluded by default.

## Indian Supreme Court Judgments — E3/E4 evidence corpus

- **Source:** [vanga/indian-supreme-court-judgments](https://github.com/vanga/indian-supreme-court-judgments), public AWS Open Data bucket `s3://indian-supreme-court-judgments/` accessed without authentication.
- **License:** CC-BY-4.0.
- **Subset loaded:** 39,073 downloaded metadata rows (33,700 distinct case IDs) and all 39,069 public-source English PDFs for 1950–2020. After the 2026-08-28 quality rebuild, 3 permanently low-quality PDFs were excluded; 39,066 usable PDFs produced 2,343,435 labeled chunks. PostgreSQL provenance and the SQLite FTS5 BM25 index contain 2,036,981 unique chunks. The requested 1947–1949 period is unavailable because the source begins in 1950.
- **Exact-date coverage:** 39,073 records with a parseable `decision_date` out of 39,073; observed dates span 1950-03-14 to 2020-12-18.
- **Fields retained for the next stage:** `title`, `petitioner`, `respondent`, `citation`, `case_id`, `decision_date`, `disposal_nature`, `court`, `path`, and `year`. The downloaded source Parquet files remain local-only.
- **Known limitations:** exact dates are present, but `case_id` can occasionally disagree with `decision_date`/citation or be absent. The source `path` is therefore retained as the mandatory stable `source_id`, alongside the original `case_id`, citation, and date; downstream audits must not infer the decision year from `case_id` alone.

## Alignment-gated crosswalk correction

- **Syntactic-ID candidate population:** 5,391 ILDC cases have a superficially matching `YYYY INSC N` eCourts identifier. This is a candidate hint only; it is not an identity claim.
- **Syntactic-ID scan:** 11 candidate pairs pass both title/party and direct six-token content alignment; 5,380 syntactic-ID candidates fail and are identifier-namespace collisions.
- **Full candidate crosswalk:** title/party fallback candidates are included in addition to syntactic candidates. Of 8,927 deduplicated candidate pairs, 1,304 are accepted by the alignment gate and 7,623 are rejected. The accepted 1,304 mappings in `corpus/dedup_matches.csv` are the authoritative replacement for the former 5,710 unvalidated mappings.
- **Standing safety controls:** retrieval excludes only an alignment-audited crosswalk mapping and also applies a direct full-query-document/sourcedocument six-token self-match check at runtime. Canonical-ID equality alone is never a self-match condition.
- **Methodological impact:** this quantified namespace collision is a standalone finding; see `artifacts/matching_root_cause.md`, `corpus/dedup_report.md`, and `corpus/dedup_alignment_rejections.csv`. Week 10 freeze and Week 11 answer-key metrics remain blocked pending source re-resolution and revalidation.

## Post-rebuild retrieval-exclusion status

- **Superseded prior audit:** the earlier canonical-ID report and `1977_183` two-chunk smoke exclusion are invalidated by the namespace-collision correction.
- **Corrected `1977_183` check:** under the alignment-gated map plus runtime content guard, the former syntactic source is not excluded and no content-aligned self-match occurs in the top-100 candidate set (`query_duplicate_chunks_excluded: 0`). This establishes that the old smoke was not evidence of safe target exclusion; true-source discovery remains required.
- **Runtime rule:** `src/legal_xai/retrieval.py` excludes only audited alignment-gated mappings and direct document-content self-matches. `src/legal_xai/evidence_pipeline.py` applies this before temporal filtering, independently of same-year exclusion.

## Week 9 authority-key provenance status

- **Evaluation coverage:** 30 of the frozen 40 ILDC fixed-test cases are now independently source-verified.
- **Authority source quality:** the ten Week 9 additions use native-text eCourts-mirror PDFs for both the query locator and the authoritative corpus source; none relies on an OCR-repaired or permanently excluded document.
- **Parallel citations:** six additions have a source-judgment reporter form that differs from the corpus SCR citation. Their stable authority source IDs and title-plus-exact-date reconciliation are recorded in `answer_key/authority_answer_key.json`.
- **Deferred selection finding:** three of the ten expected authorities were BM25 candidates but were not included in the frozen five-source selection; per-case ranks and run IDs are recorded in `artifacts/week9_answer_key_spot_checks.json` for Week 12 analysis.

## Pre-freeze dev-only retrieval investigation

- **Superseded probe:** the original eight-case probe is retained as an audit trail only. Its pre-alignment canonical-ID query-source links invalidated its 8/8 top-500 absence result as evidence of lexical mismatch.
- **Corrected probe:** nine independently verified train/validation-only cases were rebuilt from accepted alignment-gated mappings, with earlier cited eCourts authorities, source-quality checks, and direct content alignment (638--23,760 shared six-token phrases). The fixed-test answer key was not used for selection or tuning. The query-era mix is 5 cases in the 1980s and 4 in the 1990s.
- **Initial diagnosis:** all 9/9 verified authorities were absent at k=500. Facts-only inputs range from 844--19,973 words (median 5,861), while the old FTS5 query took only the first 32 terms and frequently consisted of procedural boilerplate.
- **One corrective attempt:** a deterministic full-text TF-IDF salient-term extractor was tested on the same nine dev cases at both k=100 and k=500. It moved 3/9 authorities into k=100 and 4/9 into k=500, from 0/9, but did not reach the predeclared majority-of-nine adoption threshold.
- **Final freeze decision:** keep `week7-bm25-diverse-support-v1` with candidate k=100, first-32-term FTS5 OR query, and five-source diverse selection. The first-32-term defect contributes to misses but its tested replacement was insufficient for adoption; the remaining retrieval-recall limitation is therefore bounded by evidence rather than assumed. See `artifacts/dev_retrieval_salient_terms_investigation.md`, `artifacts/dev_retrieval_probe_salient_terms.json`, and the corrected baseline artifacts.
