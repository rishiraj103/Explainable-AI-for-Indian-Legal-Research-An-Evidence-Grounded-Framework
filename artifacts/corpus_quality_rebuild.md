# eCourts corpus-quality repair and rebuild

## Discovery and scope

The initial UTF-8 audit found that the JSONL files were encoded correctly, but some source PDFs had unreadable embedded text. A full raw-PDF audit completed on 2026-08-28 across all 39,069 local PDFs (1950-2020), using fixed checks for missing embedded text, control characters, mojibake markers, ASCII-visible ratio, and English-token ratio.

- Passed native-text quality gate: 39,054 PDF instances
- Flagged for repair: 15 PDF instances, representing 14 source IDs (one local source was duplicated in two year folders)
- Pattern: primarily image-backed 1980s-1990s Supreme Court Reports with a damaged embedded-text layer; one 2018 PDF also had mojibake in its native text layer. This is a source-PDF text-layer problem, not a JSON UTF-8 bug.

## Repair policy and result

Only the 15 flagged PDF instances were rendered and OCRed with Tesseract English at 250 DPI. The same quality gate was applied to every OCR result.

- Included after OCR: 12 flagged PDF instances
- Excluded as residual low quality: 3 one-page PDFs (`S_1996_2_866_868`, `1998_1_937_947`, and `1998_1_948_960`); OCR still produced insufficient text, so no chunks were retained or indexed.

The derived corpus was then rebuilt and validated. It contains 2,343,435 chunks from 39,066 included PDFs. The three residual exclusions are explicitly listed in `corpus/ecourts/cleaning_record.json` and accepted by the corpus validator; there are no unapproved missing PDFs.

## Downstream rebuild

- PostgreSQL provenance: 2,036,981 unique chunks loaded.
- SQLite FTS5 BM25: rebuilt from that provenance set (2,036,981 indexed chunks).
- Raw PDFs are unchanged.

## Limitation

OCR is a best-effort recovery for older scanned reports and may retain minor typographical noise at page boundaries. The three documents that did not meet the fixed quality bar were excluded rather than forced into retrieval. This source-quality limitation must be reported with later retrieval results.
