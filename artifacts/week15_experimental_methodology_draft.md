# Experimental Methodology

## Experimental design and shared inputs

The executed study comprises four operational stages. E1 and E2 are outcome-prediction baselines evaluated on the same 1,503 eligible cases from the fixed ILDC test split. E3 retrieves and presents provenance-linked prior authorities for a separate, source-verified subset of 30 fixed-test cases. E4 applies hard citation, provenance, duplicate, and temporal checks to E3's displayed evidence. E3 and E4 do not emit outcome labels, so no outcome-accuracy comparison or E4-minus-E3 prediction delta is defined. This operational account supersedes any aspirational plan in which E3 or E4 was described as an outcome classifier.

E1 and E2 share the frozen `ildc-predecision-facts-v1` input rule. For each ILDC judgment, the extractor retains text preceding the earlier of a recognized closing/dispositive cue and 60% of the document, moving the boundary back to a preceding sentence end when enough text remains. A case is excluded when the retained slice is below 10% of its source text or contains fewer than 100 words. The same eligible case IDs are used by both models, and neither prediction path performs retrieval. Model and threshold selection uses the fixed validation split; the held-out test split is evaluated only after selection.

## Scope refinement from plan to implementation

The original plan described E4 as producing both an outcome prediction and an evidence-verification output. During implementation, E3 and E4 were refined into pure evidence-retrieval-and-verification pipelines because the project's primary task is legal research and evidence-backed analysis, not prediction. Outcome prediction remained exclusively within E1 and E2. This separation avoids conflating outcome classification with evidence retrieval and keeps the E3/E4 evaluation focused on authority recovery, citation validity, provenance, temporal integrity, and grounding.

"Prediction Delta (E4-E3)," as defined in the original plan, is therefore not computed, since neither E3 nor E4 produces an outcome label to compare. This is an explicit scope refinement, not a missing implemented metric.

## E1: sparse linear outcome baseline

E1 is a TF-IDF plus logistic-regression classifier fitted to the frozen facts-only text. The vectorizer uses lowercase Unicode-normalized unigrams and bigrams, sublinear term frequency, a minimum document frequency of two, L2 normalization, and at most 100,000 features. TF-IDF is fitted on eligible training inputs only. Logistic-regression regularization values `C = 0.1, 1.0, 10.0` are compared by validation accuracy, with the smaller value used to break a tie. The selected `C = 10.0` pipeline is then refitted once on eligible training and validation cases and evaluated once on the test set. The random seed is 202605.

## E2: corrected InLegalBERT chunk-and-pool baseline

E2 fine-tunes `law-ai/InLegalBERT` at pinned revision `b5ecfed8ed6cf9d25a3cb8225a8c52f161f7401a` with a newly initialized two-label classification head. The accepted implementation replaces an earlier 256-token prefix run, which had truncated 99.20% of eligible test inputs. In the corrected system, every facts-only document is tokenized into overlapping 512-token windows with 50-token overlap. The model is trained for three epochs with seed 202607, learning rate `2e-5`, weight decay 0.01, warm-up ratio 0.1, gradient checkpointing, and an effective batch size of 16 through gradient accumulation.

Predictions are aggregated at the source-document level. Mean pooling of window logits before softmax is the primary method and the checkpoint is selected only by validation document-level mean-logit accuracy. Majority vote over window predictions is retained as a secondary comparison and is not used for post-test model selection. The corrected representation covers all 1,503 eligible test documents and 9,576 test windows; no document is reduced to a single prefix.

## E3: temporally constrained retrieval and evidence presentation

E3 begins with the same frozen facts-only query text but uses it for evidence retrieval rather than outcome prediction. The final query builder, `tfidf-segment-salient-terms-v1`, segments the full input, removes procedural-report boilerplate, scores within-case terms using deterministic TF-IDF with a mild frequency factor, retains section and article cues, and emits at most 32 unique terms. These terms query a SQLite FTS5 BM25 index backed by PostgreSQL corpus provenance.

The frozen retrieval configuration is `week11-bm25-salient-terms-preranked-temporal-v3`. It admits only eCourts judgments whose decision year is strictly earlier than the ILDC query year, applying that predicate to the candidate relation before BM25 ordering and the top-100 cutoff. Same-year and missing-date items are excluded. Candidate sources are also checked against the alignment-gated ILDC/eCourts crosswalk and a direct-content self-match rule. The latter excludes a source only when at least 100 six-token phrase occurrences overlap and at least 80% of the source's unique six-token fingerprints occur in the query, which protects against target-case leakage without suppressing an earlier authority merely because the later query judgment quotes it.

From at most 100 candidates, a deterministic non-learned selector chooses up to five temporally eligible passages in descending BM25 order, with original rank as the tie-breaker and no more than one passage per source judgment. A controlled renderer then produces the legal issue, applicable authorities, verbatim supporting passages with stable provenance, an evidence-bound non-inferential conclusion, and an uncertainty statement. The renderer cannot retrieve, rerank, introduce a new authority, paraphrase a material legal proposition, or infer a case outcome.

## E4: citation and provenance verification

E4 takes the E3 answer, its retrieval-run identifier, the query identity and year, and the persisted corpus records. Each displayed item must pass five checks: the linked chunk exists in the corpus; its passage and provenance fields exactly reproduce the stored record; the chunk belongs to the recorded retrieval run; the source is neither the query judgment nor an alignment-audited duplicate; and its decision year is strictly earlier than the query year. A failed check rejects the citation rather than silently omitting the error.

Authority consistency is measured separately from citation validity. A verified displayed authority is matched to the independently constructed answer key using stable source ID, normalized citation, or normalized title plus exact decision date when the source uses a parallel reporter citation. Thus, a citation may be fully traceable and temporally valid without matching the single expected authority recorded for that query; the evaluation does not label every such alternative authority substantively irrelevant.

## Retrieval investigation and final freeze

Three bounded investigations produced the frozen E3/E4 retrieval configuration (Figure C in `artifacts/results_chapter_draft.md`). First, the legacy query builder used the first 32 terms of a case and often captured opening procedural boilerplate. Replacing it with full-input salient-term extraction moved development-probe Recall@100 from 0/9 to 3/9 under the then-current self-match rule, without changing BM25. Second, the shared-phrase self-match guard was found to suppress earlier authorities quoted at length in later judgments. Adding the 80% unique source-phrase coverage condition increased development-probe Recall@100 to 6/9 and caused the earlier broad lexical-mismatch claim to be withdrawn. Third, the unchanged strict earlier-year rule was moved from post-ranking filtering into the BM25 candidate relation. A final development consistency check reached 7/9 at k=100; on the held-out 30-case answer-key sample, this last intervention changed Recall@5 from 5/30 to 12/30 and Recall@100 from 12/30 to 15/30 without losing any of the prior 12 Recall@100 successes.

The development-probe sequence and held-out temporal comparison are not one common-population learning curve. Figure C deliberately separates the nine-case development repairs from the 30-case post-ranking-versus-pre-ranking comparison. After the pre-ranking temporal test, data versions, splits, model revisions, seeds, query construction, BM25 depth, evidence cardinality, duplicate policy, temporal rule, and renderer/verifier versions were frozen; no further retrieval tuning was permitted.

## Bundled-intervention caveat

E4 is not a single-variable causal ablation of E3. Its verification layer jointly checks corpus existence, exact passage and provenance identity, retrieval-run membership, duplicate status, and temporal eligibility. Moreover, E3 and E4 share the same final retrieval and selected evidence, and neither produces an outcome label. Consequently, any aggregate E3-to-E4 reliability difference cannot be attributed to one verification component, and the study reports no causal effect or outcome-prediction gain for that transition. The supported claim is narrower: the complete E4 verification bundle can audit whether the evidence E3 displays satisfies all frozen integrity conditions.

## Evaluation scopes

Outcome accuracy and macro F1 are computed only for E1 and E2 on 1,503 eligible fixed-test cases. Expected-authority Recall@5 and Recall@100, authority-consistency precision/recall/F1, citation groundedness, provenance validity, future-evidence exposure, and unsupported-claim checks are computed only for E3/E4 on the 30 source-verified answer-key cases. A separate seven-case, citation-parity-controlled comparison presents the same E4 evidence in structured and unstructured formats; because the only completed rating is an author self-review fallback, it is treated as descriptive explanation-format evidence rather than an independent user study. These three populations are never pooled.

## Draft provenance

This section is grounded in `config/facts_extraction.json`, `config/e1_baseline.json`, `config/e2_chunk_pool.json`, `config/evidence_selection.json`, `config/grounded_answer.json`, `config/citation_verification.json`, `artifacts/e1_baseline_results.md`, `artifacts/e2_chunk_pool_results.md`, `artifacts/e2_correction_manifest.md`, `artifacts/week9_citation_verification.md`, `artifacts/week10_reproducibility_freeze.md`, `artifacts/retrieval_investigation_summary.md`, `artifacts/week11_temporal_preranking_investigation.md`, and `artifacts/week11_reporting_framework.md`. These repository references are drafting traceability notes and can be converted to the paper's final citation style during typesetting.
