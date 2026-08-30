# Temporal Overlap Audit

This audit applies the reusable year-only ILDC temporal rule to the known ILDC/eCourts overlap candidates. It does not create a retrieval index.

- Candidate pairs assessed: 1,304
- Eligible (strictly earlier year): 116
- Ambiguous — excluded by default (same year): 1,188
- Ineligible (later year): 0
- Excluded for unresolved metadata: 0

The same-year bucket is stored separately in `temporal_ambiguities.csv` for later inspection. These pairs are also leakage candidates and must not be retrieved for their matching ILDC case.
