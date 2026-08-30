# Answer-key content-driven re-resolution

**Scope:** the ten entries flagged by the answer-key alignment audit. No
retrieval setting was changed. Every retained/replacement query case was
reconfirmed in `single_test.parquet`, uses an eCourts-mirror primary source,
and has `native-text` status (none is one of the twelve OCR-repaired or three
permanently excluded documents).

## Result

One case was corrected from the 1,304-row alignment-gated crosswalk. Four
fresh full-text discoveries were not accepted because the corresponding ILDC
record lacks enough caption/party text to satisfy the required title/party
gate; five have no aligned source in the downloaded eCourts corpus. Those nine
were transparently replaced with new fixed-test cases that satisfy both gates.

| Flagged case | Old invalid query source | Resolution | Final query case / source | Direct phrases | Title/party | Authority and parallel check |
| --- | --- | --- | --- | ---: | --- | --- |
| `2013_30` | `2013_1_243_266` | Source absent after phrase/title search; replacement | `1977_99` / `1977_3_372_388` | 3,396 | pass | *Sitaram Motilal Kalal* `[1966] 3 S.C.R. 527`; no parallel form recorded |
| `2013_35` | `2013_1_267_294` | Corrected accepted-crosswalk match | `2013_35` / `2013_1_327_335` | 1,034 | pass | *Nadodi Jayaraman* `(1992) 3 SCC 161` / `[1992] 2 S.C.R. 794`; source-ID and title/date reconciliation pass |
| `2013_57` | `2013_3_359_375` | Fresh source `2013_1_130_139` had 1,232 direct phrases but failed title/party; replacement | `1980_217` / `1980_3_1243_1252` | 1,537 | pass | *Punjab Beverages* `[1978] 3 S.C.R. 370`; no parallel form recorded |
| `2013_101` | `2013_3_392_415` | Source absent after phrase/title search; replacement | `1980_133` / `1980_3_884_892` | 1,228 | pass | *Hariprasad Shivshankar Shukla* `[1957] 1 S.C.R. 121`; no parallel form recorded |
| `2013_121` | unresolved / `2013_2_116_125` | Fresh source `2013_4_753_766` had 1,690 direct phrases but failed title/party; replacement | `1978_33` / `1978_3_131_146` | 2,271 | pass | *Daryao* `[1962] 1 S.C.R. 574`; no parallel form recorded |
| `2008_516` | `2008_6_1009_1039` | Source absent after phrase/title search; replacement | `1981_187` / `1981_3_839_848` | 1,585 | pass | *Virsa Singh* `[1958] 1 S.C.R. 1495`; no parallel form recorded |
| `2002_171` | `2002_2_808_824` | Fresh source `2002_1_775_785` had 1,556 direct phrases but failed title/party; replacement | `1980_222` / `1980_3_1127_1142` | 2,436 | pass | *Bai Tahira* `[1979] 2 S.C.R. 75`; no parallel form recorded |
| `2013_95` | `2013_1_984_995` | Source absent after phrase/title search; replacement | `1977_145` / `1977_3_428_436` | 1,245 | pass | *Devilal Modi* `[1965] 1 S.C.R. 686`; no parallel form recorded |
| `2017_14` | `2017_1_330_365` | Fresh source `2017_1_265_277` had 1,839 direct phrases but failed title/party; replacement | `1981_55` / `1981_2_910_929` | 2,832 | pass | *Nanak Chand* `[1970] 1 S.C.R. 565`; no parallel form recorded |
| `2001_414` | `S_2001_2_463_472` | Source absent after phrase/title search; replacement | `1980_105` / `1980_3_44_70` | 5,412 | pass | *Union of India v. S. B. Kohli* `[1973] 3 S.C.R. 117`; no parallel form recorded |

The specific SCC/SCR parallel citation for `2013_35` reconciles through the
existing authority-source ID path and independently through normalized title
plus exact decision date. The complete validation result is recorded in
`artifacts/answer_key_alignment_audit_corrected.{json,md}`.
