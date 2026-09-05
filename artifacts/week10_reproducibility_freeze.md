# Final Retrieval Reproducibility Freeze

This records the fixed data, model, retrieval, explanation, and safety configuration after the one permitted bounded temporal-ordering test. No further retrieval configuration changes are permitted.

- Freeze version: `week16-final-reproducibility-freeze-v3`
- ILDC split rows: train `5082`, validation `994`, test `1517`
- Retrieval configuration: `week11-bm25-salient-terms-preranked-temporal-v3`; query builder `tfidf-segment-salient-terms-v1`; candidate depth `100`; selected sources `5`.
- eCourts cleaned-corpus identity: `2343435` JSONL records in `71` files; aggregate SHA-256 `f0229bbb1242548abd57c4f8ec86a03d4edef4d2182d0ed6cbc442ee708f000f`. The full identity record is `artifacts/ecourts_corpus_identity.json`.
- Final real-answer-key query-builder regression: after repairing a quoted-authority false-positive self-match exclusion, salient TF-IDF terms were non-worsening on all six controls and retrieved/selected `2008_1629`, `1995_425`, and `2002_944` at ranks 1, 1, and 6. The complete record is `artifacts/week10_post_selfmatch_freeze_regression.json`.
- Dev-probe recheck: the coverage-qualified self-match rule recovered three further dev authorities, for 6/9 at k=100 and 7/9 at k=500; the earlier broad lexical-mismatch limitation is withdrawn. See `artifacts/week10_dev_probe_selfmatch_recheck.json`.
- Final temporal-ordering test: applying the unchanged strict earlier-year rule before BM25 ranking improved the 30-case answer-key Recall@5 from 5/30 to 12/30 and Recall@100 from 12/30 to 15/30, with no loss among the original 12 retrieval successes. It is adopted as the final configuration; see `artifacts/week11_temporal_preranking_investigation.md`.
- Temporal policy: candidate year must be strictly earlier than query year and is applied before BM25 ranking; same-year and missing-date candidates are excluded before ranking.
- Duplicate policy: alignment-gated target/near-case exclusion plus a direct source-text self-match check requiring both 100 shared six-token phrases and 80% unique candidate-source coverage.
- E1 seed: `202605`. E2 seed: `202607`.
- E1 reconstructed-model SHA-256: `60f407d85483214485b2152c05529af2c473b1a7ea59e8f0d7bb44b7409efec8`. E2 checkpoint-6318 weight SHA-256: `924a5bb9078bcc212ef07acb9f08dfaa8593e880ae3868203deb28586dbdc773`; E2 weights remain local and gitignored by design, while their hashes are tracked for verification.
- E2 correction: the former 256-token-prefix result remains recorded as discarded because 99.20% of eligible test inputs were truncated; the accepted result is the 512-token, 50-overlap chunk-and-pool run in `artifacts/e2_correction_manifest.json`.
- Environment roles: E2 checkpoint training used the Dockerfile-pinned `transformers==4.46.3`; the later host replay used `transformers==5.15.0` and reproduced exact checkpoint outputs. PostgreSQL server `16.15` and the observed `postgres:16-alpine` digest are recorded in the machine-readable freeze. Docker base-image tags remain an accepted local-research limitation; their frozen build definitions and last commit are recorded there as well.
- Answer key: `30/40` evaluation entries, with the separate dev/example record retained outside metric computation.
- The complete machine-readable freeze, including SHA-256 hashes for every frozen source, is `config/reproducibility_freeze.json`.
- The bounded replay contract is executed by `scripts/run_week10_reproducibility_replay.py`.
