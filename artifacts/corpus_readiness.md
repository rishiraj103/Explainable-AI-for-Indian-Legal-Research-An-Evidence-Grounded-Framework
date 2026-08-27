# Week 3 Corpus Readiness Verification

Verified 2026-08-27 for the eCourts English evidence corpus, 1950–2020.
No retrieval index was built during this verification.

| Check | Result |
| --- | ---: |
| Public-source English PDFs expected | 39,069 |
| Local PDFs found | 39,069 |
| eCourts metadata rows | 39,073 |
| Cleaned, labeled chunks | 2,343,407 |
| PDFs with at least one chunk | 39,069 |
| Malformed JSONL records | 0 |
| Records missing required evidence fields | 0 |
| Invalid passage character bounds | 0 |
| Chunk references without a local PDF | 0 |

## Result

The corpus is ready for Week 4 retrieval indexing. A few source archives place
a PDF in a folder whose year differs from the PDF's source year; cleaning now
resolves metadata using the PDF's stable source `path`, not its archive folder.
`case_id` is retained when supplied but is optional source metadata; `path` is
the mandatory stable `source_id` and is used in every chunk identifier.
