# Week 9 round-two salient-term retrieval correction

## Corrective scope

This is the one permitted corrective attempt after the corrected dev probe
showed that the frozen first-32-term FTS query was dominated by procedural
opening language. It changes query construction only: the BM25 index,
candidate depth, temporal policy, crosswalk exclusion, content self-match
guard, and five-source selection are unchanged. The same nine fully
alignment-gated train/validation probe cases were rerun; no test-split result
was used to design or assess the change.

## Method

`tfidf-segment-salient-terms-v1` splits the complete frozen facts-only text
into sentence/paragraph segments, removes a documented procedural-report
stoplist, scores remaining unigrams with maximum segment TF-IDF times a mild
within-document frequency factor, explicitly retains `section`/`article` and
their numeric references, and selects at most 32 unique terms. This is a
deterministic query-construction correction, not a learned reranker or a new
retrieval architecture.

## Before/after results

| Dev case | Baseline at k=500 | Salient terms at k=100 | Salient terms at k=500 |
| --- | --- | --- | --- |
| `1980_104` | absent | rank 58 | rank 58 |
| `1982_186` | absent | absent | rank 260 |
| `1984_62` | absent | absent | absent |
| `1986_70` | absent | absent | absent |
| `1988_238` | absent | absent | absent |
| `1990_651` | absent | rank 92 | rank 92 |
| `1992_137` | absent | absent | absent |
| `1992_464` | absent | rank 69 | rank 69 |
| `1993_66` | absent | absent | absent |

The correction moves 3/9 authorities into the actual k=100 candidate set and
4/9 into k=500, from 0/9 at either depth. It therefore demonstrates that
first-32-term truncation was a real contributing defect, but it does not meet
the predeclared meaningful-improvement threshold: a majority of the nine cases
must be found at k=100 or k=500.

## Round-two decision (superseded by final regression)

At this point alone, the candidate did not meet the original dev-only
majority-of-nine adoption threshold. This provisional decision is superseded
by the single final real-answer-key regression in
`artifacts/week9_final_freeze_regression.md`, which adopted the salient
extractor after it was non-worsening on all six pre-specified controls.

The remaining misses after this correction support a bounded lexical-mismatch
limitation: query truncation explains some, but not enough, of the observed
absence. Week 12 must distinguish this retrieval-recall limitation from
grounding/citation correctness for evidence that was actually retrieved.

Exact full facts inputs, constructed FTS queries, run IDs, source IDs, and
per-depth results are stored in
`artifacts/dev_retrieval_probe_salient_terms.json`; the corrected baseline is
`artifacts/dev_retrieval_probe_corrected.json`.
