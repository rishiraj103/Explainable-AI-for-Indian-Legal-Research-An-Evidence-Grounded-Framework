# Authority answer-key population clarification

Answer-key query population restricted to the ILDC fixed test split per frozen
schema. `2019_890` is not a test-split ID and is retained only as a labeled
`dev_example` case, excluded from evaluation and all metric computation.

The evaluation target is 40 distinct ILDC test-split cases. Week 9 is complete
at 30 distinct cases; Week 10 retains the frozen final pacing of 9 additional
cases. Each
candidate must pass `scripts/check_answer_key_candidate.py` against
`corpus/ildc/single_test.parquet` before any external source-verification work
begins. The full answer-key validator independently enforces the same rule for
every `evaluation` entry.

## Judgment-source policy

Live court-portal or Supreme Court Reports hosts are preferred when convenient.
The eCourts mirror is an accepted primary fallback because it is scraped from
`scr.sci.gov.in`; it is not a third-party aggregator. Every answer-key entry
that uses this mirror records `source`, `verification_method`, and `not`.
The validator rejects a mirrored source that was permanently excluded by the
Week 3 quality audit and checks that its recorded method agrees with that audit
(`native-text` or `OCR-repaired`). Third-party aggregators, case-law blogs,
summaries, and results produced by this project's retrieval system are not
acceptable authority sources.

## Week 9 expansion and retrieval spot check

Ten new fixed-test cases were added from native-text eCourts-mirror Supreme
Court Reports PDFs. Every recorded authority source is outside the Week 3
permanently excluded quality bucket; none required OCR repair. Six authority
records include a parallel reporter form (SCC, AIR, or STC in the query
judgment and SCR in the corpus). They are linked by a verified corpus source
ID and independently reconcile by normalized title plus exact decision date.

The frozen top-100 BM25 plus source-diverse five-passage selection spot check
returned two expected authorities as selected, three as retrieved-but-not-
selected (ranks 56, 75, and 96), and five outside the candidate set. The three
selection omissions are tagged for Week 12 analysis only; retrieval and
selection configuration remains frozen. See
`artifacts/week9_answer_key_spot_checks.json`.

## Content-alignment correction audit — 2026-08-30

Canonical ILDC/eCourts identifiers were found not to be sufficient proof that
the paired documents are the same judgment. Three of eight development-probe
spot reads were mismatched, triggering a read-only audit of all 30 evaluation
query-source mappings. The audit uses direct shared six-token text fingerprints
as its decisive signal, supported by party-name and subject/procedural overlap.

Results: **20 passed**, **9 resolved sources failed content alignment**, and
**1 source was unresolved**. The per-case table and side-by-side excerpts are
in `artifacts/answer_key_alignment_audit.md` and
`artifacts/answer_key_alignment_audit.json`. The ten flagged entries are not
silently removed. They must be corrected to a content-aligned eCourts source or
transparently excluded before the answer key is used for Week 11 metrics.

## Content-driven re-resolution — 2026-08-30

The ten flagged entries were rechecked against the alignment-gated crosswalk
and then against the full eCourts source text. One (`2013_35`) was corrected
from the accepted crosswalk. Four fresh text matches were rejected because the
ILDC record omits enough caption/party material that the required title/party
identity signal cannot pass; five candidates were absent from the downloaded
eCourts corpus. Those nine cases were replaced with new fixed-test cases that
pass both the title/party and direct-content gates. The answer key is again 30
evaluation cases plus the unchanged `2019_890` dev/example case. See
`artifacts/answer_key_reresolution.md`.

The 100 shared-six-token self-match floor was calibrated from the general
aligned/misaligned document-pair distribution (aligned: 372–9,199; apparent
mismatches: 0–10), not from retrieval or outcome results on the ILDC test
split. It is a leakage-safety threshold, not a test-set-tuned retrieval
parameter.

The identifier-namespace collision is concentrated in the legacy 1958–1993
portion of the corpus, where ILDC and eCourts serial-looking suffixes are
especially likely to be unrelated; numeric equality is never used as identity.
