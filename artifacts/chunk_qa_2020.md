# 2020 eCourts Chunk Quality Check

## Scope

This manual review uses a reproducible random sample of 30 chunks from the
2020 local clean run (571 PDFs, 59,732 retained chunks). The sample was drawn
with Python's `random.seed(20260827)` after cleaning version
`v1-conservative-page-text`.

## Checks and result

- **Readability and sentence-sized boundaries:** 30/30 passages were readable
  legal text; none was a standalone report header, case-title header, counsel
  list, or two-word fragment.
- **Provenance metadata:** 30/30 had `case_id`, `citation`, `decision_date`,
  `court`, `path`, PDF filename, page number, and passage character bounds.
- **Locator shape:** 30/30 used the stable
  `case_id::pPPPP::cCCC` identifier and had non-negative, ordered character
  bounds on the named PDF page.
- **Observed source-metadata anomaly:** `2017 INSC 583::p0004::c002` has a
  2020 decision date and citation. This was retained exactly as supplied,
  alongside its source `path`; it is not a cleaning error.

## Reviewed chunk identifiers

`2020 INSC 394::p0006::c003`, `2020 INSC 601::p0004::c003`,
`2020 INSC 599::p0058::c002`, `2020 INSC 238::p0020::c002`,
`2020 INSC 447::p0002::c002`, `2020 INSC 707::p0004::c006`,
`2020 INSC 264::p0127::c002`, `2020 INSC 525::p0016::c004`,
`2020 INSC 207::p0017::c003`, `2020 INSC 344::p0113::c002`,
`2020 INSC 247::p0007::c003`, `2020 INSC 376::p0075::c002`,
`2020 INSC 264::p0121::c001`, `2017 INSC 583::p0004::c002`,
`2020 INSC 130::p0093::c001`, `2020 INSC 588::p0013::c004`,
`2020 INSC 620::p0200::c003`, `2020 INSC 586::p0012::c003`,
`2020 INSC 614::p0023::c001`, `2020 INSC 184::p0009::c003`,
`2020 INSC 344::p0078::c003`, `2020 INSC 650::p0062::c004`,
`2020 INSC 498::p0052::c005`, `2020 INSC 291::p0004::c002`,
`2020 INSC 355::p0047::c002`, `2020 INSC 294::p0155::c001`,
`2020 INSC 361::p0026::c002`, `2020 INSC 589::p0026::c001`,
`2020 INSC 375::p0001::c002`, `2020 INSC 434::p0015::c001`.

## Cleaning effects observed

The original 2020 extraction produced 67,137 chunks. Conservative
document-local removal of repeated page furniture plus exclusion of logged
non-evidentiary fragments produced 59,732 chunks; 2,707 fragments were
excluded. Raw PDFs are preserved unchanged.
