# Week 9 answer-key expansion and retrieval spot check

Ten new ILDC fixed-test cases were membership-gated and source-verified against native-text eCourts-mirror Supreme Court Reports PDFs. Every authority source is outside the three permanently excluded Week 3 PDFs; none required OCR repair.

The frozen answer-key population is now **30 of 40** evaluation cases. Six gate-approved early screens were replaced because their judgment did not expose a usable earlier Supreme Court authority with a primary-source record; none was a test-split rejection.

| Retrieval/selection result | Cases |
| --- | --- |
| Retrieved and selected | `1995_412` (rank 22), `1986_397` (rank 2) |
| Retrieved but not selected | `1995_425` (rank 56), `2002_944` (rank 75), `1988_96` (rank 96) |
| Not retrieved in the frozen top-100 candidate set | `1995_403`, `1982_29`, `1994_632`, `1985_40`, `1992_84` |

The three retrieved-but-not-selected cases are deferred Week 12 selection-analysis examples. No retrieval or selection setting was changed. Six authorities use parallel reporter forms (SCC, AIR, or STC in the source judgment versus SCR in the corpus); all six were independently reconciled by title plus exact decision date, in addition to their recorded authority source IDs.

The machine-readable per-case provenance and run log is `artifacts/week9_answer_key_spot_checks.json`.
