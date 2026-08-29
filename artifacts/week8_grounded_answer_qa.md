# Week 8 E3 grounded-answer QA

## Scope and method

On 2026-08-29, five fixed topical development/QA queries were run through the
full E3 path: Week 7 temporal-safe retrieval, duplicate exclusion, deterministic
one-chunk-per-source selection, and the Week 8 controlled extract-only renderer.
The exact outputs are in `artifacts/week8_grounded_answer_qa.json`.

The renderer exposes the query as the legal issue and each selected authority's
citation and provenance. Its only material legal content is the exact selected
passage, repeated as a verbatim supported observation. It has no free-form
conclusion path. The automated grounding audit rechecked each answer against
the selected evidence before it was written.

## Results

| Query area | Selected passages | Required sections present | Grounding audit | Manual material-content check |
| --- | ---: | --- | --- | --- |
| Anticipatory bail / section 438 | 5 | Yes | Passed | Passed: every legal statement shown is a supplied passage. |
| Land-acquisition compensation | 5 | Yes | Passed | Passed: every legal statement shown is a supplied passage. |
| Arbitration agreement / arbitrator | 5 | Yes | Passed | Passed: every legal statement shown is a supplied passage. |
| NDPS recovery / seizure evidence | 5 | Yes | Passed | Passed: every legal statement shown is a supplied passage. |
| Constitutional compensation / right to life | 5 | Yes | Passed | Passed: every legal statement shown is a supplied passage. |

No sampled answer added an authority, citation, legal fact, or substantive
conclusion beyond the supplied selected evidence. Every response included the
fixed uncertainty note that it is a research brief rather than legal advice and
that missing or incomplete evidence needs human review.

## Observed limitation

The intentionally controlled renderer gives traceability priority over fluent
synthesis. Some displayed historical passages retain minor scan/extraction
artifacts from the source corpus; they remain verbatim and provenance-linked,
so this is visible to the reviewer rather than silently rewritten. Week 9 has
not yet begun: this check does not claim citation-validation or E4 provenance
enforcement beyond the existing Week 7 retrieval provenance.
