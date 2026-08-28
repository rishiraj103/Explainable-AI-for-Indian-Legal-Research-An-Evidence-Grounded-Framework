# Week 3 chunk quality check after corpus rebuild

The original Week 3 review was repeated on 2026-08-28 after the quality-gated OCR repair. The fixed sample contains 30 chunks: one from each of the 11 unique repaired source IDs and 19 seeded random chunks from passing sources (`seed=20260828`). The exact sample is stored in `artifacts/chunk_qc_rebuild_sample.json`.

| Defect category | Chunks affected (of 30) | Finding |
| --- | ---: | --- |
| Truncation | 0 | No sampled passage ended mid-token or at an extraction cut-off. |
| Mis-segmentation | 1 | One short counsel-list fragment was retained; it is a known conservative-filter false negative. |
| Missing metadata | 0 | Every sampled chunk had required provenance fields and valid ordered bounds. |
| Unreadable text | 0 | All samples, including OCR-recovered material, were legible enough to identify the legal subject. |

The single counsel-list false negative is documented as a segmentation limitation. It does not change the source-level OCR repair count or provenance locators; later retrieval QA was repeated against this exact rebuilt corpus.
