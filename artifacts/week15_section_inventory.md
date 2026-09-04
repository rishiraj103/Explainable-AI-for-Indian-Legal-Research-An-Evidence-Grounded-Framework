# Week 15 Paper-Section Inventory

## Scope and source availability

This inventory separates material adapted from the available planning excerpts from sections written from the executed project record. The Week 15 brief identifies a numbered "revised execution-plan document," but that complete document is not present in the tracked repository or available attachment set. Under the 2026-09-04 completion instruction, the paper uses the supplied scope-refinement language and Section 31 category list, the earlier frozen-plan excerpts, verified related-work sources, and the final repository evidence. It does not claim a verbatim merge from an unavailable file.

## Section status

| Paper section | Starting point | Week 15 treatment | Current status |
|---|---|---|---|
| Abstract | Revised execution-plan description plus final evidence inventory | Adapt to final findings and denominators | Complete in `artifacts/paper_draft.md` |
| Problem Definition | Available frozen-plan excerpts plus implemented scope | Reconcile with evidence-retrieval scope | Complete in `artifacts/paper_draft.md` |
| Research Gap and Novelty Positioning | Plan description plus verified related work | Retain bounded novelty claims | Complete in `artifacts/paper_draft.md` |
| Related Work | TaxFlow, CaseFacts, ILDC, InLegalBERT, and LexTime source papers | Position without cross-task metric comparison | Complete in `artifacts/paper_draft.md` |
| Research Questions | Available plan excerpts plus final operational scope | Separate outcome and evidence questions | Complete in `artifacts/paper_draft.md` |
| Hypotheses | Available plan framing plus final evidence | Preserve unsupported findings honestly | Complete in `artifacts/paper_draft.md` |
| Operational Definitions | `artifacts/week11_reporting_framework.md` | Use implemented metric definitions | Complete in `artifacts/paper_draft.md` |
| System Architecture | Executed configs and modules | Describe the final dual-branch system | Complete in `artifacts/paper_draft.md` |
| Citation and Provenance Protocol | Implemented Week 9 verifier | Preserve distinct failure states | Complete in `artifacts/paper_draft.md` |
| Responsible AI / Governance | Implemented controls and supplied plan category | Avoid claims beyond implemented safeguards | Complete in `artifacts/paper_draft.md` |
| Results and Discussion | `artifacts/results_chapter_draft.md` | Use as the Week 15 anchor | Complete starting draft |
| Limitations | Supplied Section 31 categories plus `artifacts/week14_limitations_draft.md` | Prefer evidenced Week 14 wording where categories overlap | Complete in `artifacts/week15_limitations_merged.md` and the paper |
| Introduction and Indian Legal Context | Actual project scope and verified *Pooja Ramesh Singh* judgment | Write after evidence sections stabilize | Complete in `artifacts/paper_draft.md` |
| Dataset and Legal Corpus | Executed corpus and alignment artifacts | Write fresh from the actual dual-corpus record | Drafted in `artifacts/week15_dataset_and_corpus_draft.md` |
| Experimental Methodology | Frozen configs and investigation artifacts | Write fresh from the implemented E1-E4 pipeline | Drafted in `artifacts/week15_experimental_methodology_draft.md` |
| Error Analysis | `artifacts/week12_error_analysis.md` | Adapt directly, preserving final pre-ranking buckets | Complete in `artifacts/week15_error_analysis_draft.md` and the paper |
| Conclusion | Final assembled evidence | Write last and retain bounded claims | Complete in `artifacts/paper_draft.md` |

## Evidence map for the two fresh priority sections

| Topic | Controlling source(s) |
|---|---|
| ILDC/eCourts purpose split and final corpus counts | `corpus/dataset_manifest.md`; `config/datasets.json` |
| OCR audit and targeted rebuild | `artifacts/corpus_quality_rebuild.md` |
| Identifier-namespace collision and corrected crosswalk | `artifacts/matching_root_cause.md`; `artifacts/matching_correction_checkpoint.md`; `corpus/dedup_report.md` |
| Corrected answer-key construction and era distribution | `answer_key/authority_answer_key_manifest.md`; `artifacts/answer_key_reresolution.md`; `artifacts/week14_results_evidence_inventory.json` |
| E1 implementation | `config/e1_baseline.json`; `artifacts/e1_baseline_results.md` |
| Corrected E2 implementation | `config/e2_chunk_pool.json`; `artifacts/e2_chunk_pool_results.md`; `artifacts/e2_correction_manifest.md` |
| E3 retrieval, selection, and rendering | `config/evidence_selection.json`; `config/grounded_answer.json`; `src/legal_xai/evidence_pipeline.py`; `src/legal_xai/grounded_answer.py` |
| E4 verification | `config/citation_verification.json`; `artifacts/week9_citation_verification.md`; `artifacts/week11_reporting_framework.md` |
| Final freeze and retrieval investigation | `artifacts/week10_reproducibility_freeze.md`; `artifacts/retrieval_investigation_summary.md`; `artifacts/week11_temporal_preranking_investigation.md` |

## Resolved assembly constraints

The early project plan described E4 aspirationally as including an outcome prediction. The assembled paper now records the explicit refinement: E3 retrieves, selects, and renders evidence, E4 verifies it, and outcome prediction remains in E1/E2. The Abstract, Research Questions, Hypotheses, Architecture, Methodology, Results, Governance, and Conclusion consistently follow that executed scope.

The paper must also retain three distinct evaluation populations: 1,503 eligible fixed-test cases for E1/E2 outcome prediction, 30 source-verified answer-key cases for E3/E4 evidence evaluation, and seven paired cases for the author self-review of explanation format.
