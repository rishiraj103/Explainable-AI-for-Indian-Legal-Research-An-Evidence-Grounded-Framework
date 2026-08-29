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

## Manual inspection count

- **Sample inspected:** 5 full E3 answers.
- **Clean grounding passes:** 5/5.
- **Grounding violations:** 0/5.

## Leakage and target-case exclusion status

The cross-corpus leakage audit and the target-case/near-duplicate exclusion
were verified after the 2026-08-28 corpus rebuild, before this Week 8 QA. The
rebuild smoke test sent an exact ILDC test overlap (`1977_183` / `1977 INSC
183`) through rebuilt BM25 and PostgreSQL: 2 target chunks were excluded. The
runtime retrieval path applies canonical self-match and audit-listed near-match
exclusion before its independent strict earlier-year temporal rule. Details and
split counts are recorded in `corpus/dataset_manifest.md`,
`corpus/dedup_report.md`, and `artifacts/rebuild_safety_checks.md`.
The same test was rerun on 2026-08-29 with the Week 8 pipeline; its current
output is `artifacts/week8_rebuild_exclusion_recheck.json` and again reports
`query_duplicate_chunks_excluded = 2`.

## Answer-writer test coverage

The Week 8 module has **6 focused tests** in `tests/test_grounded_answer.py`:

- supplied evidence passes the grounding audit;
- altered passages, invented authority links, and a deliberately injected
  unsupported observation are rejected;
- a one-passage answer discloses that its evidence is limited; and
- a zero-passage answer contains no authority or legal observation and states
  that it cannot reach a conclusion without fabricating support.

The full project suite passed with **40 tests** after this closeout.

## Adversarial weak-evidence check

`week8-adversarial-1950` used the query `constitutional validity fundamental
rights` with query year 1950. Since the evidence corpus begins in 1950, all 99
retrieved candidates were later-year and thus ineligible; selection returned
0 passages. The renderer produced no authority, no observation, and the
explicit insufficiency message that it cannot state a legal conclusion without
fabricating support. The exact result is
`artifacts/week8_weak_evidence_qa.json`.

## Observed limitation

The intentionally controlled renderer gives traceability priority over fluent
synthesis. Some displayed historical passages retain minor scan/extraction
artifacts from the source corpus; they remain verbatim and provenance-linked,
so this is visible to the reviewer rather than silently rewritten. Week 9 has
not yet begun: this check does not claim citation-validation or E4 provenance
enforcement beyond the existing Week 7 retrieval provenance.
