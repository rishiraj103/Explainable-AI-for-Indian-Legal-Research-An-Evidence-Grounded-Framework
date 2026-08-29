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
