# Week 10 Reproducibility Freeze

This is the pre-evaluation freeze for the fixed data, model, retrieval, explanation, and safety configuration. It does not contain Week 11 evaluation results.

- Freeze version: `week10-reproducibility-freeze-v1`
- ILDC split rows: train `5082`, validation `994`, test `1517`
- Retrieval configuration: `week10-bm25-salient-terms-selfmatch-coverage-v2`; query builder `tfidf-segment-salient-terms-v1`; candidate depth `100`; selected sources `5`.
- Final real-answer-key query-builder regression: after repairing a quoted-authority false-positive self-match exclusion, salient TF-IDF terms were non-worsening on all six controls and retrieved/selected `2008_1629`, `1995_425`, and `2002_944` at ranks 1, 1, and 6. The complete record is `artifacts/week10_post_selfmatch_freeze_regression.json`.
- Dev-probe recheck: the coverage-qualified self-match rule recovered three further dev authorities, for 6/9 at k=100 and 7/9 at k=500; the earlier broad lexical-mismatch limitation is withdrawn. See `artifacts/week10_dev_probe_selfmatch_recheck.json`.
- Temporal policy: candidate year must be strictly earlier than query year; same-year is logged as ambiguous and excluded; missing dates are excluded.
- Duplicate policy: alignment-gated target/near-case exclusion plus a direct source-text self-match check requiring both 100 shared six-token phrases and 80% unique candidate-source coverage.
- E1 seed: `202605`. E2 seed: `202607`.
- E2 correction: the former 256-token-prefix result remains recorded as discarded because 99.20% of eligible test inputs were truncated; the accepted result is the 512-token, 50-overlap chunk-and-pool run in `artifacts/e2_correction_manifest.json`.
- Answer key: `30/40` evaluation entries, with the separate dev/example record retained outside metric computation.
- The complete machine-readable freeze, including SHA-256 hashes for every frozen source, is `config/reproducibility_freeze.json`.
- The bounded replay contract is executed by `scripts/run_week10_reproducibility_replay.py`.
