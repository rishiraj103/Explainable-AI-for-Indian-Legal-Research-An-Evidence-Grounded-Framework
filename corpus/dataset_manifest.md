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
- **Standing safety controls:** retrieval excludes only an alignment-audited crosswalk mapping and also applies a direct full-query-document/source-document self-match check at runtime. Canonical-ID equality alone is never a self-match condition. The direct check requires both at least 100 shared six-token phrase occurrences and 80% unique candidate-source phrase coverage, so a later judgment's quotation of an earlier authority is not incorrectly suppressed.
- **Methodological impact:** this quantified namespace collision is a standalone finding; see `artifacts/matching_root_cause.md`, `corpus/dedup_report.md`, and `corpus/dedup_alignment_rejections.csv`. The original block was cleared after source re-resolution and corrected content-alignment revalidation; the Week 11 evaluation-round freeze is recorded below.

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
- **One corrective attempt:** a deterministic full-text TF-IDF salient-term extractor was tested on the same nine dev cases at both k=100 and k=500. Under the earlier raw self-match rule it moved 3/9 authorities into k=100 and 4/9 into k=500, from 0/9. Those figures are retained only as an audit record because the self-match rule later proved over-inclusive for quoted authorities.
- **Post-self-match dev recheck:** under `week10-bm25-salient-terms-selfmatch-coverage-v2`, 6/9 expected dev authorities are found at k=100 and 7/9 at k=500. `1984_62`, `1988_238`, and `1992_137` are newly retrieved at ranks 40, 64, and 67. The broad lexical-mismatch limitation is therefore withdrawn: the earlier absence was materially affected by false-positive self-match exclusion. `1986_70` and `1993_66` remain residual retrieval failures, but two cases do not support a corpus-wide lexical-mismatch conclusion. See `artifacts/week10_dev_probe_selfmatch_recheck.md`.
- **Affected-history note:** the raw shared-phrase self-match rule was active from leakage-hardening commit `46912df` (2026-08-30) through the coverage-qualified repair in `e96db3b`. Retrieval counts and interpretations produced in that interval may have suppressed a quoted authority and are either superseded or explicitly labelled as pre-fix audit records.
- **Rank reconciliation and final freeze decision:** the historical short issue-query ranks for `2008_1629`, `1995_425`, and `2002_944` (29, 56, and 75) reproduce on the current unchanged BM25 index. A first direct-content self-match guard incorrectly removed those quoted earlier authorities because it used only a raw shared-phrase count. The coverage-qualified repair above retains them while preserving true self-copy exclusion. The required post-fix paired regression on all six pre-specified real answer-key controls found salient terms non-worsening and retrieved/selected `2008_1629`, `1995_425`, and `2002_944` at ranks 1, 1, and 6. Adopt `week10-bm25-salient-terms-selfmatch-coverage-v2`: candidate k=100, `tfidf-segment-salient-terms-v1` query construction, coverage-qualified duplicate exclusion, and five-source diverse selection. See the before-fix and post-fix reconciliation records, `artifacts/week10_rank_reconciliation.md` and `artifacts/week10_rank_reconciliation_post_fix_v2.md`, plus `artifacts/week10_post_selfmatch_freeze_regression.json`.

## Week 11 evaluation-round reference-evidence freeze

- **Frozen at:** `2026-08-30T10:44:42.5117982Z`, from pre-evaluation commit `f6ea888d8a56352114d7ca7a672a7094854eb84c`.
- **Official reference-evidence set for this evaluation round:** 30 source-verified, fixed-test-split-confirmed, corrected-content-alignment-gated answer-key cases. The original 40-case coverage target was aspirational rather than a hard evaluation gate; the remaining 10 cases are explicitly deferred to a post-Week-11 backlog and do not block this evaluation.
- **Sanity check:** all 30/30 pass the current corrected alignment gate. Twenty cases fall in the 1958--1993 identifier-collision-risk era, and every one individually passes the corrected gate; the per-case audit is `artifacts/week11_answer_key_sanity_check.json`.
- **Metric scopes:** E1/E2 outcome prediction is reported for the 1,503 eligible cases in the full frozen ILDC test split. E3/E4 retrieval, citation, grounding, provenance, and temporal-integrity metrics are reported only for the frozen 30-case answer-key subset. E3/E4 do not emit outcome labels, so no outcome accuracy is claimed for them.
- **Initial frozen-config evaluation:** `artifacts/week11_initial_evaluation.json` and `artifacts/week11_initial_results.md` record the first quantitative run. Recall@5 is 0.166667 and Recall@100 is 0.400000 on the 30 expected authorities; the controlled pipeline's 135 displayed citations pass grounding/provenance checks, with zero temporal violations and zero unsupported-claim detections. These integrity measures certify what was displayed; they do not imply complete authority retrieval.
- **Configuration provenance and error-analysis headline:** the Week 11 E3/E4 evaluation used only `week10-bm25-salient-terms-selfmatch-coverage-v2` with `tfidf-segment-salient-terms-v1`, candidate k=100, five-source selection, strict temporal eligibility, and the coverage-qualified self-match repair. E2 references only the corrected 512-token chunk-and-pool result. The error analysis confirms the central finding: verification succeeds for retrieved evidence, while retrieval coverage is the bottleneck (11/30 expected authorities selected, 1/30 retrieved but not selected, and 18/30 absent at k=100). See `artifacts/week11_error_analysis.md`.
