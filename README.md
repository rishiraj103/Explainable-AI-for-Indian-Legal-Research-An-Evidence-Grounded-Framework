# Temporally Constrained and Provenance-Verified Legal Research

This repository contains the final Week 16 research prototype for auditable legal research over historical Indian Supreme Court judgments.  It keeps outcome prediction (E1/E2) separate from evidence retrieval, rendering, and verification (E3/E4), with frozen configurations and machine-readable artifacts for replay.

## Quick start

Install the pinned Python dependencies and make the locally stored corpus/model assets available as described in `config/reproducibility_freeze.json`:

```powershell
python -m pip install -r requirements.txt
```

### Run the demo

The demo is a static, single-user researcher interface.  It reads frozen Week 13/Week 11 artifacts and never performs live retrieval:

```powershell
python scripts/serve_week16_demo.py --port 8000
```

Open <http://127.0.0.1:8000/demo/> and keep the server terminal open.  The four representative cases are `2008_1629`, `1980_133`, `1997_792`, and `2013_35`; the interface also exposes the other fixed review cases.  See [`demo/README.md`](demo/README.md) for verification commands and scope notes.

### Run the reproducibility replay

The final clean-checkout replay contract is documented in [`config/reproducibility_freeze.json`](config/reproducibility_freeze.json) and [`artifacts/week16_reproducibility_audit.md`](artifacts/week16_reproducibility_audit.md).  With the frozen ILDC files, eCourts/PostgreSQL provenance store, BM25 index, and locally cached E2 checkpoint available, run:

```powershell
python scripts/run_week10_reproducibility_replay.py
```

The replay compares independent E4 runs after excluding generated retrieval-run UUIDs.  Large corpus, database, index, and model-cache files are intentionally gitignored; their hashes and availability contract are tracked in the freeze record.

## Where to find the final work

- **Paper and submission package:** [`submission/`](submission/), including the formatted PDF, Markdown source, figure assets, and declaration/certificate placeholders.
- **Paper source:** [`artifacts/paper_draft.md`](artifacts/paper_draft.md); the assembled Results chapter is [`artifacts/results_chapter_draft.md`](artifacts/results_chapter_draft.md).
- **Frozen reproducibility record:** [`config/reproducibility_freeze.json`](config/reproducibility_freeze.json).
- **Reproducibility audit:** [`artifacts/week16_reproducibility_audit.md`](artifacts/week16_reproducibility_audit.md).
- **Evaluation results and figures:** [`artifacts/`](artifacts/) and [`artifacts/figures/`](artifacts/figures/).
- **Source modules and evaluation scripts:** [`src/legal_xai/`](src/legal_xai/) and [`scripts/`](scripts/).
- **Demo:** [`demo/`](demo/).
- **Project completion checklist:** [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md).

## Required deliverables

The tracked repository and `submission/MANIFEST.md` cover the frozen plan's required deliverables: E1--E4 implementations, the curated retrieval index/build record, citation/provenance and explainability modules, evaluation tables/plots, error-analysis reports, reproducibility configuration/manifest, the minimal demo, the final paper, and presentation/demo instructions.  Any institution-specific candidate, supervisor, declaration, or certificate fields remain clearly marked in the included templates because no institutional template was present in the repository.

This is a research prototype, not a production legal-advice service.  It has no accounts, multi-user backend, arbitrary live-query endpoint, or automated adjudication.
