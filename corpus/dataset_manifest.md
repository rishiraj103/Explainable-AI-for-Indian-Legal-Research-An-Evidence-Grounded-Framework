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

## Leakage-audit summary

- **Exact canonical-ID overlaps (unique ILDC cases):** 5,391
- **High-confidence near title/party overlaps (unique ILDC cases):** 261
- **Unique ILDC cases flagged for exclusion review:** 5,652
- **Unique ILDC/eCourts candidate pairs flagged:** 5,710

The accompanying `dedup_report.md` records the matching method and the live overlap count. Flagged records must be excluded from retrieval candidates for the matching ILDC query case.

## Post-rebuild retrieval-exclusion status

- **Cross-corpus audit:** completed before the rebuild using canonical case-ID matching, with title/party near-duplicate fallback; ILDC has no citation field, so eCourts citations are retained as provenance rather than used as an equality key. The audit flags 1,057 exact and 59 high-confidence near ILDC-test pairs, and the same `dedup_matches.csv` identity mapping was retained through the rebuild.
- **Rebuilt-index verification:** completed 2026-08-28 and rechecked 2026-08-29 in `artifacts/rebuild_safety_checks.md`, `artifacts/rebuild_target_exclusion_smoke.json`, and `artifacts/week8_rebuild_exclusion_recheck.json`. An exact ILDC test overlap (`1977_183` / `1977 INSC 183`) was presented to the rebuilt BM25 + PostgreSQL path; 2 target-case chunks were excluded before temporal eligibility and evidence selection.
- **Runtime rule:** `src/legal_xai/retrieval.py` excludes canonical exact self-matches and every audit-listed title/party near match. `src/legal_xai/evidence_pipeline.py` applies this rule before the separate strict earlier-year temporal filter. It is therefore active for E3 retrieval, independently of same-year exclusion.

## Week 9 authority-key provenance status

- **Evaluation coverage:** 30 of the frozen 40 ILDC fixed-test cases are now independently source-verified.
- **Authority source quality:** the ten Week 9 additions use native-text eCourts-mirror PDFs for both the query locator and the authoritative corpus source; none relies on an OCR-repaired or permanently excluded document.
- **Parallel citations:** six additions have a source-judgment reporter form that differs from the corpus SCR citation. Their stable authority source IDs and title-plus-exact-date reconciliation are recorded in `answer_key/authority_answer_key.json`.
- **Deferred selection finding:** three of the ten expected authorities were BM25 candidates but were not included in the frozen five-source selection; per-case ranks and run IDs are recorded in `artifacts/week9_answer_key_spot_checks.json` for Week 12 analysis.

## Pre-freeze dev-only retrieval investigation

- **Probe population:** eight independently source-verified ILDC train-only cases in `answer_key/dev_retrieval_probe.json`; the validator enforces `split: dev`, train/validation membership, exclusion from the fixed test split, strict temporal eligibility, and no use of permanently excluded sources.
- **Alignment correction:** on 2026-08-30, manual side-by-side reads confirmed that 3 of 8 original dev probes (37.5%) did not align their ILDC text with the canonically ID-matched eCourts query document. The apparent 8/8 top-500 absence is therefore preserved as an audit record, **not** treated as evidence of lexical mismatch or a final retrieval-freeze result.
- **Triggered evaluation audit:** the read-only audit in `artifacts/answer_key_alignment_audit.md` checked all 30 real evaluation query-source mappings using direct six-token text fingerprints, with party-name and subject/procedural signals as supplementary checks. Twenty mappings passed; nine resolved eCourts sources failed content alignment; one source could not be resolved. No answer-key entry, retrieval configuration, or metric was silently changed.
- **Current status:** `config/evidence_selection.json` remains unchanged. Before a valid dev-only retrieval investigation can be rerun, the matching root cause and a permanent content-alignment gate must be implemented, then all flagged evaluation mappings must be corrected or transparently excluded.
