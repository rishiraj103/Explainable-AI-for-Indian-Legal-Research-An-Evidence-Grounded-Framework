# Authority answer-key population clarification

Answer-key query population restricted to the ILDC fixed test split per frozen
schema. `2019_890` is not a test-split ID and is retained only as a labeled
`dev_example` case, excluded from evaluation and all metric computation.

The evaluation target is 40 distinct ILDC test-split cases. None are complete
yet: the Week 7--10 pacing remains 10, 10, 10, and 9 cases respectively. Each
candidate must pass `scripts/check_answer_key_candidate.py` against
`corpus/ildc/single_test.parquet` before any external source-verification work
begins. The full answer-key validator independently enforces the same rule for
every `evaluation` entry.
