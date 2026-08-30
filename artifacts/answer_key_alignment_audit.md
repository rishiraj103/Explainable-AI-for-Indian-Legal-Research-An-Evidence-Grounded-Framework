# Evaluation answer-key content-alignment audit

Read-only audit of all 30 evaluation entries after the dev-probe misalignment catch. A pass requires at least 100 direct shared six-token phrases between the fixed-test ILDC text and its resolved eCourts query-source document. This conservative threshold follows the observed separation: aligned documents have 372–9,199 shared phrases, while apparent mismatches have 0–10. Party-name and subject/procedural term signals are supplementary; side-by-side opening excerpts are recorded in JSON for every row.

**Result:** 30 total; fail_content_mismatch: 9, fail_unresolved_source: 1, pass: 20

| ILDC case | Resolved eCourts source | Resolution | Direct phrases | Party signal | Subject/posture signal | Status |
| --- | --- | --- | ---: | --- | --- | --- |
| `2008_1629` | `2008_15_694_705` | source_id_from_eCourts_URL | 1289 | True | True | pass |
| `1997_792` | `S_1997_3_266_321` | source_id_from_eCourts_URL | 9199 | True | True | pass |
| `1995_322` | `1995_3_217_226` | source_id_from_eCourts_URL | 1513 | False | True | pass |
| `1993_185` | `1993_2_353_368` | source_id_from_eCourts_URL | 2393 | True | True | pass |
| `1971_295` | `1972_1_184_192` | source_id_from_eCourts_URL | 825 | True | True | pass |
| `1974_36` | `1974_3_464_469` | source_id_from_eCourts_URL | 697 | True | True | pass |
| `1995_375` | `1995_3_426_429` | source_id_from_eCourts_URL | 372 | True | True | pass |
| `1986_176` | `1986_3_378_382` | source_id_from_eCourts_URL | 603 | True | True | pass |
| `1986_378` | `1986_2_187_229` | source_id_from_eCourts_URL | 6444 | True | True | pass |
| `1984_136` | `1984_3_752_762` | source_id_from_eCourts_URL | 1040 | True | True | pass |
| `2013_30` | `2013_1_243_266` | title_and_exact_date | 5 | False | True | fail_content_mismatch |
| `2013_35` | `2013_1_267_294` | title_and_exact_date | 0 | False | True | fail_content_mismatch |
| `2013_57` | `2013_3_359_375` | title_and_exact_date | 0 | False | True | fail_content_mismatch |
| `2013_101` | `2013_3_392_415` | title_and_exact_date | 0 | False | True | fail_content_mismatch |
| `2013_121` | `—` | unresolved_source | — | — | — | fail_unresolved_source |
| `2008_516` | `2008_6_1009_1039` | title_and_exact_date | 3 | False | True | fail_content_mismatch |
| `2002_171` | `2002_2_808_824` | title_and_exact_date | 0 | True | True | fail_content_mismatch |
| `2013_95` | `2013_1_984_995` | source_id_from_eCourts_URL | 0 | True | True | fail_content_mismatch |
| `2017_14` | `2017_1_330_365` | source_id_from_eCourts_URL | 10 | True | True | fail_content_mismatch |
| `2001_414` | `S_2001_2_463_472` | source_id_from_eCourts_URL | 0 | True | True | fail_content_mismatch |
| `1995_412` | `1995_3_1004_1036` | source_id_from_eCourts_URL | 4670 | True | True | pass |
| `1995_403` | `1995_3_1197_1234` | source_id_from_eCourts_URL | 7254 | True | True | pass |
| `1995_425` | `1995_3_932_942` | source_id_from_eCourts_URL | 1746 | True | True | pass |
| `2002_944` | `2002_1_888_896` | source_id_from_eCourts_URL | 1467 | True | True | pass |
| `1986_397` | `1986_3_553_561` | source_id_from_eCourts_URL | 1125 | True | True | pass |
| `1982_29` | `1982_3_251_276` | source_id_from_eCourts_URL | 3574 | True | True | pass |
| `1994_632` | `S_1994_4_35_51` | source_id_from_eCourts_URL | 2699 | True | True | pass |
| `1985_40` | `1985_2_832_850` | source_id_from_eCourts_URL | 2432 | True | True | pass |
| `1992_84` | `1992_1_481_529` | source_id_from_eCourts_URL | 6542 | True | True | pass |
| `1988_96` | `1988_3_248_254` | source_id_from_eCourts_URL | 865 | True | True | pass |
