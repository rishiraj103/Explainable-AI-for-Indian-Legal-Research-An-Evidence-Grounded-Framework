# Evaluation answer-key content-alignment audit

Read-only audit of all 30 evaluation entries after the namespace-collision correction. A content-alignment pass requires at least 100 direct shared six-token phrases between the fixed-test ILDC text and its resolved eCourts query-source document. The direct threshold was calibrated from the general aligned/misaligned document-pair distribution, not test-split outcomes. The title/party gate is reported separately because some legacy ILDC text records omit the judgment caption; every corrected or replacement entry in the current correction satisfies both gates. Side-by-side opening excerpts are recorded in JSON for every row.

**Result:** 30 total; pass: 30

| ILDC case | Resolved eCourts source | Resolution | Direct phrases | Title/party gate | Subject/posture signal | Status |
| --- | --- | --- | ---: | --- | --- | --- |
| `2008_1629` | `2008_15_694_705` | source_id_from_eCourts_URL | 1289 | False | True | pass |
| `1997_792` | `S_1997_3_266_321` | source_id_from_eCourts_URL | 9199 | False | True | pass |
| `1995_322` | `1995_3_217_226` | source_id_from_eCourts_URL | 1513 | False | True | pass |
| `1993_185` | `1993_2_353_368` | source_id_from_eCourts_URL | 2393 | False | True | pass |
| `1971_295` | `1972_1_184_192` | source_id_from_eCourts_URL | 825 | True | True | pass |
| `1974_36` | `1974_3_464_469` | source_id_from_eCourts_URL | 697 | True | True | pass |
| `1995_375` | `1995_3_426_429` | source_id_from_eCourts_URL | 372 | False | True | pass |
| `1986_176` | `1986_3_378_382` | source_id_from_eCourts_URL | 603 | False | True | pass |
| `1986_378` | `1986_2_187_229` | source_id_from_eCourts_URL | 6444 | True | True | pass |
| `1984_136` | `1984_3_752_762` | source_id_from_eCourts_URL | 1040 | True | True | pass |
| `1977_99` | `1977_3_372_388` | source_id_from_eCourts_URL | 3396 | True | True | pass |
| `2013_35` | `2013_1_327_335` | source_id_from_eCourts_URL | 1034 | True | True | pass |
| `1980_217` | `1980_3_1243_1252` | source_id_from_eCourts_URL | 1537 | True | True | pass |
| `1980_133` | `1980_3_884_892` | source_id_from_eCourts_URL | 1228 | True | True | pass |
| `1978_33` | `1978_3_131_146` | source_id_from_eCourts_URL | 2271 | True | True | pass |
| `1981_187` | `1981_3_839_848` | source_id_from_eCourts_URL | 1585 | True | True | pass |
| `1980_222` | `1980_3_1127_1142` | source_id_from_eCourts_URL | 2436 | True | True | pass |
| `1977_145` | `1977_3_428_436` | source_id_from_eCourts_URL | 1245 | True | True | pass |
| `1981_55` | `1981_2_910_929` | source_id_from_eCourts_URL | 2832 | True | True | pass |
| `1980_105` | `1980_3_44_70` | source_id_from_eCourts_URL | 5412 | True | True | pass |
| `1995_412` | `1995_3_1004_1036` | source_id_from_eCourts_URL | 4670 | False | True | pass |
| `1995_403` | `1995_3_1197_1234` | source_id_from_eCourts_URL | 7254 | True | True | pass |
| `1995_425` | `1995_3_932_942` | source_id_from_eCourts_URL | 1746 | False | True | pass |
| `2002_944` | `2002_1_888_896` | source_id_from_eCourts_URL | 1467 | False | True | pass |
| `1986_397` | `1986_3_553_561` | source_id_from_eCourts_URL | 1125 | True | True | pass |
| `1982_29` | `1982_3_251_276` | source_id_from_eCourts_URL | 3574 | True | True | pass |
| `1994_632` | `S_1994_4_35_51` | source_id_from_eCourts_URL | 2699 | True | True | pass |
| `1985_40` | `1985_2_832_850` | source_id_from_eCourts_URL | 2432 | False | True | pass |
| `1992_84` | `1992_1_481_529` | source_id_from_eCourts_URL | 6542 | False | True | pass |
| `1988_96` | `1988_3_248_254` | source_id_from_eCourts_URL | 865 | False | True | pass |
