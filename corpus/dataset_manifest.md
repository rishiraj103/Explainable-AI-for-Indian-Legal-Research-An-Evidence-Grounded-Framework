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
- **Subset loaded:** 39,073 downloaded metadata rows (33,700 distinct case IDs) and all 39,069 public-source English PDFs for 1950–2020. Conservative cleaning produced 2,343,407 labeled chunks; no retrieval index has been built. The requested 1947–1949 period is unavailable because the source begins in 1950.
- **Exact-date coverage:** 39,073 records with a parseable `decision_date` out of 39,073; observed dates span 1950-03-14 to 2020-12-18.
- **Fields retained for the next stage:** `title`, `petitioner`, `respondent`, `citation`, `case_id`, `decision_date`, `disposal_nature`, `court`, `path`, and `year`. The downloaded source Parquet files remain local-only.
- **Known limitations:** exact dates are present, but `case_id` can occasionally disagree with `decision_date`/citation or be absent. The source `path` is therefore retained as the mandatory stable `source_id`, alongside the original `case_id`, citation, and date; downstream audits must not infer the decision year from `case_id` alone. No retrieval index has been built.

## Leakage-audit summary

- **Exact canonical-ID overlaps (unique ILDC cases):** 5,391
- **High-confidence near title/party overlaps (unique ILDC cases):** 261
- **Unique ILDC cases flagged for exclusion review:** 5,652
- **Unique ILDC/eCourts candidate pairs flagged:** 5,710

The accompanying `dedup_report.md` records the matching method and the live overlap count. Flagged records must be excluded from retrieval candidates for the matching ILDC query case.
