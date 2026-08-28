# Week 4 BM25 retrieval quality check after corpus rebuild

The fixed 20-query review was repeated on 2026-08-28 against the rebuilt FTS5 BM25 index and rebuilt PostgreSQL provenance records. Each query requested 30 candidates and returned its first three temporally eligible passages.

- Queries reviewed: 20
- Queries with subjectively relevant eligible top-k evidence: 19
- Queries with no eligible evidence: 1
- Temporal leakage returned as evidence: 0

The manual relevance rate is **19/20 (95%)**. The single no-result query was `elephant corridor environmental protection`: all 30 lexical matches were relevant 2020 material, and the frozen year-only policy correctly placed them in the `ambiguous_excluded` bucket rather than returning them as evidence.

The same failure pattern is therefore a limitation of year-only temporal eligibility and lexical retrieval, not a corpus-corruption or provenance failure. All reviewed results point to stable case, citation, PDF, page, and passage locators.
