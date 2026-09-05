# Required-deliverable manifest

| Required deliverable | Included location | Status / note |
| --- | --- | --- |
| E1 outcome-prediction implementation | `../scripts/train_e1_baseline.py`, `../scripts/reconstruct_e1_predictions.py`, `../src/legal_xai/` | Included in source tree; frozen config and results are tracked. |
| E2 outcome-prediction implementation | `../scripts/train_e2_chunk_pool_cached.py`, `../scripts/infer_e2_checkpoint_predictions.py`, `../config/e2_chunk_pool.json` | Included; checkpoint weights remain locally cached by design and are hash-recorded in the freeze. |
| E3 retrieval and evidence-selection implementation | `../src/legal_xai/retrieval.py`, `../src/legal_xai/evidence_pipeline.py`, `../scripts/run_evidence_pipeline.py` | Included; final selection configuration is frozen. |
| E4 citation/provenance verification implementation | `../src/legal_xai/citation_verifier.py`, `../src/legal_xai/grounded_answer.py`, `../scripts/run_grounded_answer_pipeline.py` | Included; exact passage, provenance, duplicate, and temporal checks are tracked. |
| Curated retrieval index | `../retrieval/bm25.sqlite` (local), `../artifacts/bm25_index.json` (tracked build record) | The multi-gigabyte SQLite index is gitignored; its hash and build record are frozen. |
| Citation/provenance module | `../src/legal_xai/citation_verifier.py`, `../scripts/load_provenance.py`, `../config/citation_verification.json` | Included. |
| Explainability module | `../src/legal_xai/grounded_answer.py`, `../demo/` | Included, with the static researcher-facing demo. |
| Evaluation tables and plots | `../artifacts/e1_e2_comparison.*`, `../artifacts/week11_temporal_prerank_evaluation.json`, `figures/` | Included; figures 1–5 are copied for the paper. |
| Error-analysis report | `../artifacts/week12_error_analysis.md`, `../artifacts/week15_error_analysis_draft.md` | Included. |
| Reproducibility configuration and manifest | `../config/reproducibility_freeze.json`, `../artifacts/week16_reproducibility_audit.md` | 14/14 documentation checks and 34/34 freeze hashes passed. |
| Minimal demo and instructions | `../demo/README.md`, `../scripts/serve_week16_demo.py` | Included; static, local, single-user scope. |
| Final paper | `paper.pdf`, `paper.md` | PDF plus editable source included. |
| Presentation/demo script | `../demo/README.md`, `../artifacts/week16_demo.png` | Launch and verification instructions plus reference screenshot included. |
| Declaration/certificate pages | `declaration_template.md`, `certificate_template.md` | Neutral placeholders included because no institutional template was supplied. |
