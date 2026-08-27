# Week 4 BM25 Retrieval Quality Check

## Method

Twenty fixed legal queries from `config/retrieval_qa_queries.json` were run
against the FTS5 BM25 index. Each run requested 30 candidates, stored every
rank and temporal status in PostgreSQL, then reviewed the first three
temporally eligible results. All query cases use 2020 as the year-only ILDC
query context, so 2020 precedents are correctly excluded as ambiguous.

## Result

- **Queries reviewed:** 20
- **Queries with 2–3 relevant eligible results:** 19
- **Queries with no eligible result:** 1
- **Temporal leakage returned as evidence:** 0

The one no-result query was **elephant corridor environmental protection**.
All 30 highest BM25 matches were highly relevant chunks from a 2020 Supreme
Court judgment, so the frozen year-only policy placed every one in the
`ambiguous_excluded` bucket. This is expected behavior: the system preserves
those matches in PostgreSQL for inspection but does not return them as evidence.

## Manual relevance summary

| Query area | Assessment |
| --- | --- |
| Anticipatory / regular bail | Relevant CrPC sections 438 and 439 passages |
| Land acquisition / motor accident | Relevant compensation authorities |
| Consumer protection / arbitration / insolvency | Relevant statutory and procedural authorities |
| Tax / customs export unit / NDPS | Relevant tax, export-unit, and seizure evidence |
| FIR / property gifts / medical admission / service law | Relevant criminal procedure and subject-matter authorities |
| Probate / workplace harassment / trial evidence | Relevant probate, Vishakha/2013 Act, and Evidence Act material |
| Vehicle insurance / Article 21 compensation | Relevant Motor Vehicles Act and constitutional-rights authorities |

Income-tax results included one accident-compensation passage discussing an
income-tax deduction; the next two were directly about income tax. This is a
minor lexical-ranking limitation to revisit after the Week 4 checkpoint, not a
temporal or provenance failure.
