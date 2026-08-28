# eCourts extraction-quality scope audit

Audited all 39069 locally available raw PDFs across 71 years.

## Result

- Pass: 39054
- Needs repair: 15
- Reasons: insufficient_embedded_text=3, mojibake_markers=6, unicode_control_characters=11

The fixed quality bar is recorded in the JSON companion file. A `needs_repair` result means the current native-text extraction must not enter the rebuilt retrieval corpus without an approved fallback or explicit exclusion.

## Flagged documents

| Source ID | Year | Pages | Image pages | Reasons |
| --- | ---: | ---: | ---: | --- |
| 1981_2_185_265 | 1980 | 81 | 81 | unicode_control_characters |
| 1981_2_185_265 | 1981 | 81 | 81 | unicode_control_characters |
| 1981_2_516_532 | 1981 | 17 | 17 | unicode_control_characters, mojibake_markers |
| 1981_2_615_636 | 1981 | 22 | 22 | unicode_control_characters, mojibake_markers |
| 1983_2_249_270 | 1983 | 22 | 22 | unicode_control_characters |
| 1983_2_676_683 | 1983 | 8 | 8 | unicode_control_characters |
| S_1985_2_131_301 | 1985 | 171 | 171 | unicode_control_characters, mojibake_markers |
| S_1985_2_936_948 | 1985 | 13 | 13 | unicode_control_characters, mojibake_markers |
| S_1988_1_411_424 | 1988 | 14 | 14 | unicode_control_characters |
| S_1994_1_136_162 | 1994 | 27 | 27 | unicode_control_characters, mojibake_markers |
| S_1994_1_693_713 | 1994 | 21 | 21 | unicode_control_characters |
| S_1996_2_866_868 | 1996 | 1 | 0 | insufficient_embedded_text |
| 1998_1_937_947 | 1998 | 1 | 0 | insufficient_embedded_text |
| 1998_1_948_960 | 1998 | 1 | 0 | insufficient_embedded_text |
| 2018_12_654_671 | 2018 | 18 | 0 | mojibake_markers |
