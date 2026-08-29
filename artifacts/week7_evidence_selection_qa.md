# Week 7 evidence-selection usefulness check

Five fixed legal queries were run on 2026-08-28 through the Week 7 pipeline:
BM25 candidate retrieval, temporal eligibility and duplicate exclusion, then
the deterministic one-chunk-per-source selector. The exact results are in
`artifacts/week7_evidence_selection_qa.json`.

These are topical development/QA prompts, not ILDC case IDs and not entries in
the frozen test-split authority answer-key population. They assess retrieval
usefulness only and are excluded from all answer-key coverage and evaluation
metrics.

| Query area | Selected sources | Human usefulness assessment |
| --- | ---: | --- |
| Anticipatory bail / section 438 | 5 | All five passages directly concern anticipatory bail, section 438, or the relationship to regular bail. |
| Land acquisition compensation | 5 | All five passages directly address land-acquisition compensation, valuation, or statutory factors. |
| Arbitration agreement / arbitrator | 5 | All five passages directly address an arbitration agreement, referral, or arbitrator process. |
| NDPS recovery / seizure evidence | 5 | All five passages are on NDPS recovery, search, seizure, contraband, or evidentiary procedure. |
| Constitutional compensation / right to life | 5 | Three passages are directly useful constitutional-compensation or Article 21 authorities; two are broader constitutional-rights context. |

All five queries produced a small, traceable evidence set that a human reader
can inspect. The constitutional-compensation result shows the known lexical
ranking limitation: source diversity prevents repeated passages from one case,
but it does not guarantee every selected passage is equally specific. This is
recorded for later evaluation rather than adjusted after inspection.
