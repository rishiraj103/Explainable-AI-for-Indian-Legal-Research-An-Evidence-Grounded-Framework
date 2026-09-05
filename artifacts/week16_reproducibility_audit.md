# Week 16 Final Reproducibility Audit

Audit time: `2026-09-04T17:15:20+05:30`  
Audited commit: `af28d5ca5c0c5fa8defb2cf2b9d05334557c1187` (`main` and `origin/main` matched before the audit)

## Documentation checklist

The pass criterion is strict: the requested information must be explicit in a tracked file, not recoverable only from the current machine or project memory.

| Item | Result | Explicit tracked location | Audit note |
| --- | --- | --- | --- |
| Dataset version and split: ILDC Single and eCourts | **FAIL** | `config/reproducibility_freeze.json` -> `datasets_and_splits`; `config/datasets.json`; `corpus/dataset_manifest.md` | ILDC source revision, fixed split rows, and all three Parquet hashes are explicit. The effective eCourts cleaning record and BM25 index are hashed, and the manifest gives source/counts, but no immutable upstream eCourts snapshot revision or aggregate raw/cleaned-corpus hash/database dump hash is recorded. `config/datasets.json` also retains the stale pre-rebuild cleaned count `2,343,407`, while the final manifest/cleaning record reports `2,343,435`. A fresh clone cannot identify or reconstruct the exact PostgreSQL corpus from Git alone. |
| Preprocessing/tokenization and Week 5 facts-only rule | **PASS** | `config/reproducibility_freeze.json` -> `datasets_and_splits.ildc_single.facts_extraction`; `config/facts_extraction.json`; `config/e1_baseline.json` -> `tfidf`; `config/e2_chunk_pool.json` -> `model` and `input` | The facts-only rule is versioned as `ildc-predecision-facts-v1`, declared frozen before E1 fitting, hashed by the freeze, and shared by E1/E2. E1 tokenization and E2 model revision/windowing are explicit. |
| Model checkpoints: E1 reconstruction and E2 checkpoint-6318 | **FAIL** | `corpus/dataset_manifest.md` -> Prediction-recovery correction; `artifacts/e1_test_predictions.json`; `artifacts/e2_chunk_pool_results.json` -> `best_checkpoint`; `artifacts/e2_test_predictions.json` | Both identities and reconstruction/inference procedures are written down, but the freeze omits the E1 reconstructed model and E2 checkpoint artifacts and hashes. E2 weights are gitignored. Machine-local hashes observed during this audit are E1 joblib `60f407d85483214485b2152c05529af2c473b1a7ea59e8f0d7bb44b7409efec8` and E2 `model.safetensors` `924a5bb9078bcc212ef07acb9f08dfaa8593e880ae3868203deb28586dbdc773`; recording them here does not make the missing weights available from a clean clone. |
| BM25 settings and query construction | **PASS** | `config/reproducibility_freeze.json` -> `experiments.E4.retrieval_selection`; `config/evidence_selection.json`; `scripts/build_bm25_index.py`; `artifacts/bm25_index.json` | Final configuration `week11-bm25-salient-terms-preranked-temporal-v3`, salient-term construction, SQLite FTS5 BM25 engine, `unicode61 remove_diacritics 2` tokenizer, index version, and index hash are explicit. |
| Passage segmentation | **PASS** | `corpus/ecourts/cleaning_record.json` -> `chunking`; `src/legal_xai/corpus.py` -> `chunk_page_text`; `scripts/clean_and_chunk_ecourts.py` | Page-bound, sentence-aligned chunks are capped at 220 words and four sentences; page number and character offsets are retained. The freeze hashes the cleaning record. |
| Top-k retrieval depth | **PASS** | `config/reproducibility_freeze.json` -> `experiments.E4.retrieval_selection.candidate_k`; `config/evidence_selection.json` | Candidate depth is exactly 100; the displayed support-set cap is five. |
| Evidence-selection rule | **PASS** | `config/reproducibility_freeze.json` -> `experiments.E4.retrieval_selection`; `config/evidence_selection.json`; `src/legal_xai/evidence_pipeline.py` | Descending BM25 order, original-rank deterministic tie-break, strictly eligible candidates, at most one chunk per source, and at most five selected items are explicit. |
| Random seeds | **PASS** | `config/reproducibility_freeze.json` -> `experiments.E1.random_seed` and `experiments.E2_corrected.random_seed`; `config/e1_baseline.json`; `config/e2_chunk_pool.json` | E1 uses `202605`; E2 uses `202607`. Retrieval and rendering are deterministic and do not define a stochastic seed. |
| Training hyperparameters | **PASS** | `config/e1_baseline.json` -> `tfidf`, `logistic_regression`, and `selection_protocol`; `config/e2_chunk_pool.json` -> `training`, `input`, fallback, and `selection_protocol`; both configs are hashed in the freeze | E1 C search/refit protocol and E2 epochs, learning rate, weight decay, warmup, batch/accumulation, checkpointing, fp16, optimizer, windowing, pooling, and checkpoint-selection rule are explicit. |
| Evaluation reference-evidence construction | **PASS** | `config/reproducibility_freeze.json` -> `experiments.E4.answer_key`; `config/week11_evaluation_round.json` -> `reference_evidence_set`; `artifacts/week11_answer_key_sanity_check.json`; `answer_key/authority_answer_key_manifest.md` -> Content-alignment correction and Temporal balance | The 30-case fixed-test set, source/content-alignment gate, 30/30 membership/alignment checks, and era distribution (including 13/30 in the 1980s and 20 collision-risk-era cases) are explicit. |
| Citation matching and parallel-citation reconciliation | **PASS** | `config/reproducibility_freeze.json` -> `experiments.E4.citation_verifier.answer_key_measurement`; `config/citation_verification.json`; `src/legal_xai/citation_verifier.py` -> `evaluate_against_answer_key`; `artifacts/week9_answer_key_spot_checks.md` | Verified source ID is primary; normalized title plus exact decision date reconciles parallel reporter citations. Six such cases are documented. |
| Temporal eligibility implementation | **PASS** | `config/reproducibility_freeze.json` -> `experiments.E4.retrieval_selection` and `temporal_policy`; `config/evidence_selection.json`; `src/legal_xai/evidence_pipeline.py` -> `temporal_preranked_bm25_sql` | The strict earlier-year rule is applied before ranking/top-100; same-year and missing-date candidates are excluded. |
| Provenance schema | **PASS** | `scripts/load_provenance.py` -> `SCHEMA_SQL`; `config/citation_verification.json` -> `required_checks` | The tracked schema explicitly defines `corpus_chunks`, `retrieval_runs`, and `retrieval_results`, including stable source/chunk IDs, citation/date/title, PDF/page/character locators, chunk text, rank, BM25 score, temporal status, and run linkage. |
| Software dependencies, PostgreSQL, and Docker images | **FAIL** | `config/reproducibility_freeze.json` -> `environment`; `requirements.txt`; `compose.yaml`; `docker/Dockerfile.ocr`; `docker/e2.Dockerfile` | Host Python and several package versions are frozen, and Docker tags are present. However, the final training/runtime dependency set is split and inconsistent (`transformers` 5.15.0 in the host freeze versus 4.46.3 in the E2 image); `requirements.txt` omits torch/transformers/pytest; `postgres:16-alpine` and base images are mutable tags without digests; and the exact PostgreSQL server patch (`16.15` observed locally) is not written in a tracked record. |

Documentation result: **11 PASS, 3 FAIL**. The failing items are the eCourts snapshot/database identity, checkpoint artifact hashing/availability, and exact environment/container pinning.

Freeze-integrity check: **24/24 existing path/SHA-256 pairs passed** against the current local files; there were zero missing files and zero hash mismatches. This confirms that the freeze is internally intact where it does provide hashes, but does not cure the missing identities above.

## First clean-checkout replay: defect found

A fresh GitHub clone of `origin/main` at commit `af28d5ca5c0c5fa8defb2cf2b9d05334557c1187` was used. The clone began clean. Because the required large assets are intentionally untracked, the replay supplied the original hash-checked ILDC Parquet files, local E2 cached test windows/checkpoint, local BM25 index, dedup crosswalk, and the running PostgreSQL corpus. This is a clean-code checkout replay, not a proof that Git alone can reconstruct the environment.

One uninterrupted replay covered all final experiment paths:

- E1 deterministic reconstruction and prediction on all 1,503 eligible test cases: exact record-for-record match; accuracy `0.613440`, macro-F1 `0.612342`.
- E2 inference from `checkpoint-6318` over all 9,576 cached windows / 1,503 cases: exact record-for-record match for both pooling rules; mean-logit accuracy `0.596806`, macro-F1 `0.592358`.
- E3/E4 retrieval, five-source selection, controlled rendering, citation/provenance verification, and answer-key scoring on all 30 cases: aggregate metrics match exactly — Recall@5 `0.40`, Recall@100 `0.50`, authority precision/recall/F1 `0.08/0.40/0.133333`, citation groundedness/provenance `1.0/1.0`, temporal-violation and unsupported-claim rates `0.0/0.0`, with 150 displayed citations.

Strict end-to-end replay result: **FAIL (qualified)**. Stable per-case output differs in one field for all 12 retrieved-and-selected cases. The replay populates `expected_authority_retrieved_not_selected` for those selected authorities, whereas the frozen artifact correctly leaves that field empty. `scripts/run_week11_initial_evaluation.py` computes a retrieval-only `key_measure` with `checks=()` at line 153 and writes this field from that measurement at line 196; it should use the selected/displayed measurement for this field. All other stable per-case fields, all 30 case IDs/order, every E1/E2 prediction, and every aggregate metric reproduced.

Replay output SHA-256 values (temporary clean-clone artifacts):

- E1 predictions: `9af1cad0313d604259680ceeccb020f56c17afa704179615ed207be54b660ca4`
- E2 predictions: `43f33a3931302335ec22c441877b54cebcac606191740a657057424bb72cc733`
- E3/E4 full evaluation: `f681de6818f750f6e974d2dbd8d9a9a83f9fdcceb8e6855c1fa1c56267fb49f6`

The replay validated the published frozen metrics, predictions, retrieval outcomes, grounding, provenance, and temporal results, but did **not** satisfy strict full-payload reproducibility. This first replay is retained as the defect record and is superseded for replay status by the re-verification below.

## Second clean-checkout replay: fix applied and verified

On `2026-09-05T08:59:02+05:30`, the runner was corrected so `expected_authority_retrieved_not_selected` is written from `selected_measure["expected_authorities_retrieved_not_selected"]`, rather than the retrieval-only `key_measure`. The retrieval-only measure remains in use for Recall@5 and Recall@100; only the displayed-selection classification changed.

A second fresh clean clone of corrected commit `bc70006a44f64a5cef1b208c8737eefa8f797d8e` repeated the same E1 reconstruction, E2 checkpoint inference, and 30-case E3/E4 evaluation using the same hash-checked local assets.

- All 12 retrieved-and-selected cases now have an empty `expected_authority_retrieved_not_selected` list.
- Only the three genuine retrieved-but-not-selected cases remain populated: `1980_133`, `1981_55`, and `1985_40`.
- E1 and E2 replay files are byte-identical to the first replay: `9af1cad0313d604259680ceeccb020f56c17afa704179615ed207be54b660ca4` and `43f33a3931302335ec22c441877b54cebcac606191740a657057424bb72cc733`, respectively.
- E3/E4 aggregate metrics, case order, predictions, and every other stable per-case field are identical to the first replay. Excluding generated retrieval run UUIDs, the only 12 differences are the repaired field values. When both UUIDs and that repaired field are excluded, the old and new canonical payload SHA-256 values are identical: `beb683cbaaa71d41a590c61060613af55f2ee799225d05eacc11ff949f090e95`.

Corrected replay output SHA-256 values:

- E1 predictions: `9af1cad0313d604259680ceeccb020f56c17afa704179615ed207be54b660ca4`
- E2 predictions: `43f33a3931302335ec22c441877b54cebcac606191740a657057424bb72cc733`
- E3/E4 full evaluation: `247583501287767687c6ab32f9ad487c74c9a1048bbd83a021f30e36b7d84d5b`
- E3/E4 canonical stable payload excluding generated run UUIDs: `7257e6a5a1c78d7c028e252f9ebcafb02a5d31630b5cdc05becb0b9ca608b6b6`

Final clean-checkout replay status: **PASS**. The three outstanding documentation-completeness findings remain open, but the runner bookkeeping defect is fixed and its full evaluation replay now reproduces the audited results exactly apart from generated run UUIDs and the intentionally corrected field.
