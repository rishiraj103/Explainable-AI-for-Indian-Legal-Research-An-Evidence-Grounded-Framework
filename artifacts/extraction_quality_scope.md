# eCourts extraction-quality scope audit

Audited 145 raw PDFs across 71 available years using a seeded stratified sample plus four known problem files.

## Result

- Pass: 142
- Needs repair: 3
- Reasons: mojibake_markers=3, unicode_control_characters=2

The fixed quality bar is recorded in the JSON companion file. A `needs_repair` result means the current native-text extraction must not enter the rebuilt retrieval corpus without an approved fallback or explicit exclusion.

## Flagged documents

| Source ID | Year | Pages | Image pages | Reasons |
| --- | ---: | ---: | ---: | --- |
| 1981_2_516_532 | 1981 | 17 | 17 | unicode_control_characters, mojibake_markers |
| S_1994_1_136_162 | 1994 | 27 | 27 | unicode_control_characters, mojibake_markers |
| 2018_12_654_671 | 2018 | 18 | 0 | mojibake_markers |
