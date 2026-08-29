# Authority answer-key population clarification

Answer-key query population restricted to the ILDC fixed test split per frozen
schema. `2019_890` is not a test-split ID and is retained only as a labeled
`dev_example` case, excluded from evaluation and all metric computation.

The evaluation target is 40 distinct ILDC test-split cases. Week 7 and Week 8 are complete
at 20 distinct cases; Week 9 and Week 10 retain the frozen pacing of 10 and 9 additional
cases respectively. Each
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
