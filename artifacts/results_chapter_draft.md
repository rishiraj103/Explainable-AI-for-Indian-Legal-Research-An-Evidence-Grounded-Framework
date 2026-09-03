# Results Chapter Draft

## Scope and reporting populations

This section draws only from `artifacts/week14_results_evidence_inventory.json` and its Markdown rendering. The project reports three separate populations: 1,503 eligible fixed ILDC test cases for outcome prediction; 30 source-verified answer-key-covered cases and 150 displayed citations for authority recovery and verification; and seven fixed paired cases for explanation-format review. These populations are not aggregated or treated as a common denominator.

## Outcome prediction

On the 1,503-case outcome-prediction population, the TF-IDF logistic-regression baseline (E1) achieved accuracy of 0.6134 and macro F1 of 0.6123. The corrected InLegalBERT E2 mean-logit result achieved accuracy of 0.5968 and macro F1 of 0.5924. Both results exceeded the majority-class accuracy baseline of 0.5017, while E1 led corrected E2 on this frozen task. E3 and E4 are not outcome classifiers, so no E4-minus-E3 prediction delta is reported.


![Figure A. Outcome prediction comparison](figures/week14_figure_a_outcome_prediction.svg)

*Figure A. Outcome-prediction comparison on the frozen eligible ILDC test population (n=1,503).*

## Authority recovery, grounding, and temporal integrity

On the 30-case source-verified answer-key subset, expected-authority Recall@5 was 0.40 (12/30) and Recall@100 was 0.50 (12 selected + 3 retrieved-but-unselected = 15/30 found within k=100). The final buckets were 12 cases where the expected authority was retrieved and selected, three where it was retrieved but not selected, and 15 where it was absent at k=100. Authority-consistency precision was 0.080000, recall was 0.400000, and F1 was 0.133333. Its structural ceiling comes from the fixed citation cardinality, not the 12 observed matches: 150 displayed citations / 30 cases = 5 citations per case, so one answer-key authority per case yields a ceiling of 1/5 = 0.200000. The observed precision is therefore 40% of that ceiling. The superseded post-ranking round displayed 135/30 = 4.5 citations per case, whereas the final pre-ranking round displays 150/30 = 5.0; this expected shift follows the pre-ranking temporal filter preventing ineligible candidates from consuming candidate depth and is not a red flag. These recovery figures are distinct from verification: all 150 displayed citations were grounded, provenance-valid, and temporally eligible, with zero temporal violations and zero unsupported claims. The result therefore supports a bounded claim: verification succeeds for displayed evidence, while recovery of the predefined authority remains incomplete.


![Figure B. Expected-authority recovery funnel](figures/week14_figure_b_retrieval_funnel.svg)

*Figure B. Expected-authority recovery funnel on the 30-case source-verified answer-key subset (n=30).*

![Figure D. Displayed-evidence integrity](figures/week14_figure_d_integrity_summary.svg)

*Figure D. Displayed-evidence integrity under the final frozen configuration (n=30 queries; 150 displayed citations).*

## Retrieval mechanism behind the final result

The final recall figures followed three bounded changes recorded in the inventory. First, query construction changed from the legacy first-32-term form to deterministic TF-IDF salient terms drawn from the full facts-only input, removing opening procedural boilerplate without changing BM25. Second, the shared-phrase self-match guard was repaired by retaining the 100 shared-six-token floor and requiring 80% unique source-phrase coverage; the corrected development probe recovered three additional authorities. Third, the strict earlier-year temporal rule was applied before BM25 ranking and the top-100 cutoff. That final change improved held-out Recall@5 from 5/30 to 12/30, Recall@100 from 12/30 to 15/30, and selected expected authorities from 11/30 to 12/30, without losing an original retrieval success.


![Figure C. Retrieval investigation](figures/week14_figure_c_retrieval_investigation.svg)

*Figure C. Retrieval investigation pathway: development repairs and the held-out temporal comparison.*

## Explanation-format observation

The seven-case paired explanation-format review was an author self-review fallback, not independent reviewer evidence. In that descriptive sample, the structured display was preferred in 7/7 cases. Mean source-clarity ratings were 4.57 for structured presentation and 2.71 for unstructured presentation. The self-review identified navigation and triage of apparent retrieval noise as perceived advantages of the structured display. These findings describe perceived explanation quality only; they do not establish legal correctness or generalize to independent users.


![Figure E. Explanation-format review](figures/week14_figure_e_explanation_review.svg)

*Figure E. Explanation-format rubric means from the Week 13 author self-review fallback (n=7 paired cases; not independent evidence).*
