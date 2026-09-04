# Limitations and Threats to Validity

## English-language and source scope

The study covers English-language Indian Supreme Court judgments in ILDC Single and the English PDF collection available through the eCourts-derived archive. It does not evaluate Hindi or other Indian-language judgments, High Court or lower-court material, statutes as a separately versioned corpus, or cross-jurisdictional transfer. Conclusions are therefore limited to the two source collections and tasks evaluated here.

## Corpus extraction and facts-only approximation

The eCourts source audit found 15 affected PDF instances among 39,069. Targeted OCR restored 12, while three one-page PDFs remained below the fixed quality threshold and were excluded. OCR-repaired passages may still contain minor typographical noise. For ILDC, the deterministic facts-only rule has no gold-standard facts/reasoning boundaries: it can retain pre-decision legal reasoning or omit factual material near a boundary. The rule is reproducible and was manually checked on a fixed sample, but it remains an approximation rather than a semantic annotation.

## Answer-key size and era concentration

The authority-recovery evaluation uses 30 source-verified cases rather than the originally aspirational 40. The corrected subset is era-skewed: 13/30 query cases are from the 1980s, compared with five from the 1970s, nine from the 1990s, two from the 2000s, and one from the 2010s. The retrieval findings should therefore be read as results for this source-verified subset, not as an era-balanced characterization of Indian legal research or the full ILDC test split.

## Reference-authority coverage

Each evaluation query credits one independently verified expected authority. The key supports reproducible recovery measurement, but it is not an exhaustive list of every legally relevant authority. Of the 150 displayed citations, 138 did not match that single expected authority; without independent substantive relevance labels, those citations cannot be classified as legally irrelevant merely because they differ from the key. Authority consistency and citation validity must therefore remain separate measures.

## Residual authority-recovery gap

Temporal pre-ranking improved retrieval but did not explain all remaining misses. Case `2013_35` remained absent despite 79 eligible candidates in its former raw top 100, whereas `1980_105` was recovered despite only three eligible raw candidates and became a top-five hit after the final filter. Eligible-pool size and lexical relevance or authority-ranking quality are therefore independent contributing factors. Perfect verification of displayed citations must not be interpreted as complete expected-authority recovery.

## Year-level temporal granularity

ILDC query dates are available only through the year encoded in each case ID. The enforced rule is consequently strict earlier decision year, not day-level ordering. Same-year authorities are excluded as ambiguous even when an exact date might make them historically available. The final evaluation establishes compliance only with this conservative year-level rule; it does not support claims about finer chronology, changes in precedential treatment, or provision-level statutory validity.

## Bundled verification layer

E4 jointly applies corpus-existence, exact-passage, provenance, retrieval-run membership, duplicate, and temporal checks. The evaluation shows the behavior of that complete verification bundle but does not isolate the causal contribution of any one component. This is a component-attribution constraint on the implemented evidence pipeline, not an outcome-classification result.

## Explanation-quality evidence is not independent

The Week 13 review is a seven-case, non-random author self-review fallback. Its 7/7 structured preference and descriptive ratings cannot be presented as independent human-review evidence, statistically generalizable usability evidence, or evidence of legal correctness. It remains a documented design observation rather than a finding about independent legal or non-legal reviewers.

## Boilerplate uncertainty language

For `2013_35`, the self-review found that both formats used identical generic uncertainty language despite comparatively coherent evidence. The warning was visually clear but substantively uncalibrated: it signaled the same caution level as cases containing apparent retrieval noise. This is a system-level limitation rather than a format-specific defect.

## Semester-scale evaluation

The project is a semester-scale research prototype, not a production legal-research service. Its controlled scope limits the breadth of models, retrieval methods, answer-key annotation, independent review, and deployment testing. The results establish the behavior of the frozen implementation and evaluation samples; they do not establish operational reliability across users, courts, legal domains, or changing corpora.

## Draft provenance

The evidenced categories above are adapted from `artifacts/week14_limitations_draft.md`, `artifacts/corpus_quality_rebuild.md`, `artifacts/facts_extraction_validation.md`, `artifacts/week11_temporal_prerank_evaluation.json`, `artifacts/week12_error_analysis.md`, `artifacts/week13_review_summary.md`, and `artifacts/week14_results_evidence_inventory.json`. The English-language and semester-scale categories are retained as general scope statements without invented empirical detail.
