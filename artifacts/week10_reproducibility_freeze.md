# Week 10 Reproducibility Freeze

This is the pre-evaluation freeze for the fixed data, model, retrieval, explanation, and safety configuration. It does not contain Week 11 evaluation results.

- Freeze version: `week10-reproducibility-freeze-v1`
- ILDC split rows: train `5082`, validation `994`, test `1517`
- Retrieval configuration: `week10-bm25-salient-terms-v1`; query builder `tfidf-segment-salient-terms-v1`; candidate depth `100`; selected sources `5`.
- Temporal policy: candidate year must be strictly earlier than query year; same-year is logged as ambiguous and excluded; missing dates are excluded.
- Duplicate policy: alignment-gated target/near-case exclusion plus direct six-token source-text self-match exclusion.
- E1 seed: `202605`. E2 seed: `202607`.
- Answer key: `30/40` evaluation entries, with the separate dev/example record retained outside metric computation.
- The complete machine-readable freeze, including SHA-256 hashes for every frozen source, is `config/reproducibility_freeze.json`.
- The bounded replay contract is executed by `scripts/run_week10_reproducibility_replay.py`.
