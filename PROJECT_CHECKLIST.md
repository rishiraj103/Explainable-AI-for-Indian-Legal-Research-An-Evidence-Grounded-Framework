# Indian Legal XAI Project Checklist

Project progress tracker. It is committed only when the user has explicitly approved it alongside real completed work.

## Week 1 — Completed

- [x] Set up the Git repository and local progress tracking.
- [x] Confirm the ILDC dataset access route.
- [x] Select NyayaAnumana as the fallback dataset.
- [x] Define the initial legal-data handling rule.
- [x] Freeze the three research questions.
- [x] Define the initial evidence/provenance fields.

## Week 2 — Tool and Dataset Decisions

- [x] Run feasibility checks on one or two legal-language models.
- [x] Select one legal-language model for the project.
- [x] Confirm the final dataset: ILDC or the fallback dataset.
- [x] Record the chosen dataset's subset, approximate case count, fields, and usage restrictions.
- [x] Freeze the temporal-eligibility rule, including how missing dates are handled.
- [x] Confirm that both the model and data source are selected before Week 3.

## Week 3 — Clean and Organize Legal Documents

- [x] Confirm the raw-document acquisition scope and available local storage before downloading eCourts judgment PDFs.
- [x] Implement deterministic cleaning for raw legal text while preserving source text separately.
- [x] Segment legal documents into passage-sized chunks with stable identifiers and source locators.
- [x] Attach required metadata to every chunk: source ID, court/issuer, citation, decision/effective date, and passage boundary.
- [x] Run a manual quality check on at least 30 sampled chunks and record any defects found.
- [x] Confirm that the cleaned, labeled corpus is ready for Week 4 retrieval indexing.

## Week 4 â€” Build the Search System

- [x] Add reusable temporal availability metadata/filtering to retrieved evidence, preserving the frozen same-year exclusion rule.
- [x] Build a BM25 index over the cleaned eCourts chunks without changing their provenance.
- [x] Store chunk provenance and retrieval-rank records in PostgreSQL.
- [x] Implement top-k retrieval that applies temporal filtering before returning evidence.
- [x] Manually assess the top results for 20â€“30 realistic legal queries and record the findings.
- [x] Confirm the search system is functioning and ready for Week 5.

## Week 5 — Build the E1 Prediction Baseline

- [x] Inspect ILDC's fixed splits and define a reproducible facts-only input rule.
- [x] Define and validate the frozen shared rule: use the earlier of a closing/outcome cue or the 60% positional cap; sentence-align cuts; exclude slices below 10% retention or 100 words. Reviewed 30 deterministic samples (seed 202605): no target-outcome wording observed; one early-disposition outlier was excluded.
- [x] Build TF-IDF + Logistic Regression using only those facts.
- [x] Use the supplied train/validation/test roles without tuning on the test split; select C on validation only, then refit train+validation once.
- [x] Permanently record split counts, source and eligible-ID hashes, preprocessing, seed, package versions, and model settings.
- [x] Run the locked E1 baseline on the test split: accuracy 0.6134, macro F1 0.6123, with C=10.0 selected on validation.
- [x] Contextualize E1: the 50.17% majority-class baseline is exceeded by 11.18 points; audit the 87/7,593 (1.15%) exclusions for length, labels, years, boundary causes, and broad header-derived case type.
- [x] Verify the baseline can be reproduced from its saved code, configuration, and results: an unchanged rerun produced identical JSON and Markdown SHA-256 hashes.

## Week 6 — Build E2 and Start the Authority Answer Key

- [x] Confirm the frozen InLegalBERT revision, pinned container package versions, and GPU training limits: Docker can access the RTX 3050 (4 GB); use max length 256, batch size 2, and gradient checkpointing.
- [x] Fine-tune the chosen legal-language model on exactly the shared, frozen facts-only E1 inputs, without retrieval or evidence lookup.
- [x] Select training settings on validation only; use the test split only for the locked final E2 evaluation.
- [x] Record E2 metrics and compare them honestly with E1 and the majority baseline: E2 test accuracy 0.5695 and macro F1 0.5575, 4.39 points below E1 accuracy (0.6134); it still exceeds the 50.17% majority baseline.
- [x] Audit the preliminary E2 result: validation accuracy improved from 0.5005 to 0.5727 across all three epochs; the saved best checkpoint was evaluated; the test confusion matrix predicts both labels. However, 1,491/1,503 test inputs (99.20%) were truncated at 256 tokens and 1,454/1,503 (96.74%) exceed InLegalBERT's 512-token limit.
- [x] Correct the documented E2 long-document issue with 512-token overlapping chunk-and-pool inference; retain the 256-token result as discarded, and record corrected mean-logit accuracy 0.5968 and macro F1 0.5924 with 100% test-document coverage.
- [x] Define a source-first answer-key schema and inclusion standard independent of this system's retrieval output.
- [x] Retain `2019_890` as a three-authority, official-PDF-verified development example only; it is excluded from evaluation and metric computation.
- [x] Freeze the answer-key target at 40 ILDC test-split query cases, paced as 10 in Week 7, 10 in Week 8, 10 in Week 9, and 9 in Week 10; the evaluation count starts at 0/40.
- [x] Confirm E2 and the initial answer key are ready for the next planned week.

## Week 7 - Connect Search Results to the Evidence Pipeline

- [x] Build a reusable retrieval-to-evidence pipeline that accepts a legal query and returns temporally eligible, provenance-linked candidate chunks.
- [x] Implement and document a deterministic evidence-selection rule that narrows candidates to a small, non-redundant support set.
- [x] Run five fixed end-to-end evidence-selection checks and manually assess whether the selected support is useful and relevant.
- [x] Add 10 independently sourced and validated query-case entries to the authority answer key, following the frozen schema and source-first rule. (10/10 complete)
- [x] Confirm that the narrowed evidence is useful for a human reader before starting Week 8 grounded answer generation.

## Week 8 - Retrieval-Grounded Legal Research (E3)

- [x] Freeze the E3 answer-writer design and its evidence-only constraint; retain the Week 7 retrieval, selection, date, and duplicate-exclusion configuration unchanged.
- [x] Implement a controlled answer renderer that accepts only the selected evidence set and produces a structured legal-research brief.
- [x] Require every output to show the legal issue, retrieved authorities, verbatim evidence passages with provenance, and an uncertainty/missing-evidence note.
- [x] Add automated grounding checks that reject generated evidence claims or citations not present in the supplied selected evidence.
- [x] Run and manually inspect a fixed sample of grounded answers; log whether any material answer content exceeds the evidence supplied to it.
- [x] Continue the source-first authority answer key with 10 additional ILDC fixed-test-split cases, following the frozen source policy and pre-verification membership gate. (10/10 complete; 20/40 fixed-test cases total)
- [x] Confirm E3 is evidence-grounded and ready for Week 9 citation verification; do not implement Week 9 validation rules yet. (Leakage exclusion rechecked on rebuilt index; adversarial no-evidence behavior and grounding tests completed.)

## Week 9 - Citation and Evidence Verification (E4 foundation)

- [x] Define the citation-verification contract for each answer citation: corpus existence, exact passage/provenance, retrieval-run membership, and strict temporal eligibility.
- [x] Implement a reusable verifier that rejects missing corpus records, altered passages, citations not returned for the query, query-duplicate sources, and later/same-year authorities.
- [x] Wire the verifier to the frozen source-first answer key to measure supported authority retrieval separately from fabricated or wrong citations.
- [x] Continue the frozen answer-key pacing with 10 additional independently verified ILDC fixed-test-split cases. (10/10 completed; target 30/40 total. Per-case retrieval/selection spot checks recorded.)
- [x] Create and run 10-15 deterministic hand-authored pass/fail citation-verification tests, including deliberately fake, wrong-passage, non-retrieved, temporal, and duplicate failures. (13 tests; all passed.)
- [x] Run a real E3 answer through the verifier and record the result with provenance. (Run 8ec4fdc9-809d-4b40-940d-4c2c7fb369b6: 5/5 citations verified; the frozen expected authority was reported as not retrieved.)
- [x] Confirm the citation and evidence verification module is ready for Week 10; do not implement Week 10 explanation/freeze work yet. (Week 9 answer-key coverage 30/40; full suite 56 passed.)
- [x] Rebuild the invalidated dev probe from alignment-gated train/validation mappings and complete the bounded k=500 investigation. (9/9 verified authorities absent; configuration kept as-is with an evidence-backed lexical-mismatch limitation; corrected artifact and 65-test suite recorded.)
- [x] Complete the one permitted salient-term query correction on the same nine dev cases. (TF-IDF full-facts extraction improved 0/9 to 3/9 at k=100 and 4/9 at k=500; the provisional non-adoption was superseded by the final fixed-control regression below.)
- [x] Complete the final non-iterative real-answer-key query-builder regression. (Salient terms were non-worsening on all six fixed controls and improved 1988_96 from absent to rank 13; adopted as the Week 10 frozen query-construction method.)

## Week 10 - Explain Outputs Clearly and Freeze the Configuration

- [x] Define and enforce the fixed E4 explanation order: legal issue, applicable authorities, supporting evidence, conclusion, then any uncertainty/missing-evidence note. The conclusion is fixed non-inferential wording linked only to displayed evidence IDs.
- [x] Verify strict temporal eligibility is active in the full E4 retrieval-to-explanation path, not only as a standalone helper. A 2020 smoke run logged 30 same-year candidates as ambiguous/excluded and citation verification accepted all five selected earlier authorities. The direct self-match rule was then corrected to require 80% unique candidate-source phrase coverage, preventing a valid quoted precedent from being excluded.
- [x] Create one reproducibility-freeze record covering dataset/corpus versions, fixed split hashes, facts-extraction rule, E1/E2 settings and seeds, BM25/index settings, query construction, selection settings, temporal and duplicate-exclusion policies, and environment versions.
- [x] Perform a bounded reproducibility replay of one representative pipeline run and record whether its structured output and provenance reproduce. Two independent runs matched after excluding only generated run UUIDs.
- [x] Recheck the nine-case dev retrieval probe after the coverage-qualified self-match repair. Three additional authorities were recovered; the earlier broad lexical-mismatch conclusion is withdrawn and preserved only as a superseded pre-fix audit record.
- [x] Run the full test suite and freeze validation; commit the real Week 10 work and its checklist entry without beginning Week 11 evaluation. (Post-reconciliation suite and bounded replay re-run before final commit.)

## Week 11 - Run the Full Held-Out Evaluation

- [x] Freeze the evaluation populations before scoring: E1/E2 use the 1,503 eligible fixed-test cases; E3/E4 citation/grounding measures use the 30-case source-verified answer-key subset. The planned 40 was aspirational; the remaining 10 are a post-Week-11 backlog item.
- [x] Reconcile the frozen E1 and corrected E2 baselines on the 1,503-case held-out population; retain E2 mean-logit pooling as primary and majority vote as a secondary report.
- [x] Run frozen E3 retrieval and evidence selection on the 30 covered test queries; measure expected-authority recall, including retrieved-but-not-selected versus absent authorities.
- [x] Run frozen E4 verified explanations on the same 30 queries; measure citation validity, grounding, temporal-rule violations, and unsupported claims.
- [x] Compile the initial side-by-side E1/E2/E3/E4 result table with per-row denominators, frozen configuration identifiers, and no post-test tuning.
- [ ] If a human explanation-readability review is planned, prepare the outreach/materials now; do not treat it as a metric until the planned later review stage.
- [x] Run evaluation validation and commit the real evaluation artifacts. The scoped E1/E2 and E3/E4 result sets are complete; `pytest -q` is constrained to the project `tests/` suite to avoid collecting the local model cache. Do not begin Week 12 analysis.
- [x] Complete the final bounded temporal-ordering test: pre-rank strictly earlier authorities before BM25 top-100, adopt it after Recall@5 improved 5/30 to 12/30 and Recall@100 improved 12/30 to 15/30 with no regression among the prior 12 successes, then freeze the result.

## Week 12 - Analyze Successes, Failures, and Limits

- [x] Freeze the finalized Week 11 result record as the only input to Week 12 analysis; do not tune or rerun any system based on the test findings.
- [x] Categorize all 30 answer-key-covered cases into expected authority retrieved-and-selected, retrieved-but-not-selected, and absent-at-k=100 buckets.
- [x] Deterministically reconstruct frozen E1 (C=10.0, fixed train+validation facts-only data) and run inference-only E2 from checkpoint-6318; both exactly reproduce the frozen metrics and retain per-case predictions. E1/E2 disagreements: full n=1,503: 238 E1-only correct, 213 E2-only correct; cohort n=30: 3 each.
- [x] Separate provenance-valid citation status from answer-key authority consistency; do not call an alternative citation irrelevant without a human relevance label.
- [x] Record temporal-integrity outcomes and at least one honest retrieval/selection limitation for the results discussion.
- [x] Finalize the Week 12 error-analysis table and commit it without changing frozen evaluation settings. No chart is required to communicate the three exhaustive retrieval buckets.
- [x] Close Week 12 with the recovered E1/E2 prediction join and final mandatory-category table. Categories requiring an E3/E4 outcome prediction are explicitly marked structurally inapplicable; 0-instance categories are recorded as zero rather than inferred.
- [x] Reconcile Week 12 against the final pre-ranking retrieval freeze: 12/30 selected, 3/30 retrieved-but-not-selected, and 15/30 absent at k=100; preserve the three-round retrieval investigation summary for Discussion/Limitations.

## Week 13 - Human Review of Explanation Quality

- [x] Prepare a fixed seven-case RQ3 paired ablation packet that compares structured evidence-linked briefs with the exact same evidence in unstructured presentation, using the final Week 11 freeze and shuffled per-case display order.
- [x] Prepare a structured response template covering source clarity, ease of locating provenance, appropriate trust, uncertainty clarity, and comparative preference; retain a programmatic citation-parity audit for all seven pairs.
- [x] Complete the delayed self-review fallback because no outside reviewer was available; preserve the blank response template and label the completed response as author self-review rather than independent evidence.
- [x] Summarize ratings and qualitative feedback honestly: structured was preferred 7/7, with narrow advantages in the two thematically coherent cases and wider advantages where evidence contained apparent relevance noise; the seven-case non-random sample and author-review status limit interpretation.
- [x] Commit the completed Week 13 feedback record without modifying system outputs or frozen settings.

## Week 14 - Synthesize Results and Draft the Research Report

- [x] Define Week 14 as a read-only synthesis stage: consolidate final E1/E2, E3/E4, Week 12, and Week 13 evidence without rerunning or tuning the system.
- [x] Build a consolidated results-evidence inventory with every metric's source artifact, denominator, and permitted interpretation.
- [x] Draft an RQ-aligned findings outline that separates outcome prediction, authority recovery/verification, and explanation-format observations.
- [x] Assemble the Results and Discussion draft from frozen artifacts only: retain distinct populations, show final authority-recovery arithmetic and precision ceiling, document the retrieval mechanism, and label the Week 13 finding as author self-review rather than independent evidence.
- [x] Write an initial limitations and threats-to-validity draft covering answer-key era concentration, residual retrieval limitations, year-only temporal granularity, boilerplate uncertainty, and author self-review bias; retain OCR/corpus limits for the later cross-artifact final check.
- [x] Perform a final cross-artifact consistency check for metrics, denominators, configuration identifiers, and superseded results.
- [x] Commit the Week 14 synthesis artifacts without modifying model, retrieval, answer-key, or evaluation outputs. (`92809a9`, pushed with local `main`, `origin/main`, and GitHub `main` aligned.)

## Week 15 - Assemble the Full Paper Draft

- [x] Inventory the paper sections that should be adapted from the revised execution plan versus sections requiring fresh project-specific writing; record that the revised-plan source document is not currently present in the repository or available attachments.
- [x] Draft the Dataset and Legal Corpus section from the executed dual-corpus record: ILDC for E1/E2, eCourts for E3/E4, the 15-PDF-instance OCR audit and repair, the identifier-namespace collision, the alignment gate, and the corrected 30-case answer key with its era distribution.
- [x] Draft the Experimental Methodology section from the frozen implementation: shared facts-only inputs, E1, corrected E2 chunk-and-pool, E3 retrieval and controlled evidence presentation, E4 verification, the three-round retrieval investigation, and the bundled-intervention caveat.
- [x] Resolve the unavailable full revised-plan source using the scope-refinement language and Section 31 category list supplied in the completion task, the available frozen-plan excerpts, verified related-work sources, and final project evidence; disclose that no verbatim comparison with the unavailable file was possible.
- [x] Merge the supplied Section 31 categories with `artifacts/week14_limitations_draft.md`, preferring evidence-backed wording and retaining English-only and semester-scale limits as unpadded general statements.
- [x] Draft the Error Analysis section directly from the final pre-ranking `artifacts/week12_error_analysis.md` record.
- [x] Write the Introduction and Indian Legal Context after the evidence sections stabilized, using the verified *Pooja Ramesh Singh* framing without expanding the project's demonstrated claims.
- [x] Assemble the adapted and fresh sections into `artifacts/paper_draft.md`, using `artifacts/results_chapter_draft.md` as the Results and Discussion anchor.
- [x] Write the Conclusion last and limit it to the final supported findings: 150/150 verified citations, 15/30 Recall@100, the seven-case author self-review observation, and E1 outperforming corrected E2 on the frozen outcome task.
- [x] Read the assembled paper end-to-end and resolve contradictions in experiment definitions, claims, denominators, configuration identifiers, novelty framing, and superseded results; record the passing checks in `artifacts/week15_consistency_check.md`.
- [x] Commit and push the completed Week 15 paper artifacts; confirm local `main`, `origin/main`, and GitHub `main` match.
