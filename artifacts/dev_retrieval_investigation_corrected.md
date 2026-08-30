# Corrected Week 9 dev-only retrieval investigation

## Scope and validity

This investigation supersedes the earlier eight-case probe, whose query-source
links predated the alignment gate and were therefore invalid for retrieval
conclusions. It uses nine ILDC train/validation cases only, each selected from
the accepted 1,304-row content-driven crosswalk. No fixed-test ID, fixed-test
answer-key entry, test result, or retrieval configuration was used to select
the probe or make the decision below.

Every query source passed the title/party and direct six-token content gates
(638--23,760 full shared phrases), every expected authority is earlier than
the query, all sources are native-text eCourts-mirror documents, and none is
one of the three permanently excluded PDFs. The dev-probe validator confirms
that all nine IDs are outside the fixed ILDC test split.

The query-era distribution is 5/9 cases in the 1980s and 4/9 in the 1990s.
This remains legacy-heavy, but is less concentrated than the corrected
evaluation answer key; it is recorded as a coverage constraint rather than a
representative sample claim.

## Step 1 - Corrected dev probe and source verification

| Dev case | Split | Aligned query source | Expected authority source | Citation used to verify in query source | Authority corpus citation |
| --- | --- | --- | --- | --- | --- |
| `1980_104` | train | `1980_3_207_223` | `1979_2_699_716` | `[1979] 2 S.C.R. 699` | `[1979] 2 S.C.R. 699` |
| `1982_186` | validation | `1982_3_75_80` | `1980_1_736_758` | `[1980] 1 S.C.R. 736` | `[1980] 1 S.C.R. 736` |
| `1984_62` | train | `1984_3_118_161` | `1964_3_164_190` | `[1964] 3 S.C.R. 164` | `[1964] 3 S.C.R. 164` |
| `1986_70` | train | `1986_2_278_387` | `1981_2_111_154` | `[1981] 2 S.C.R. 111` | `[1981] 2 S.C.R. 111` |
| `1988_238` | train | `S_1988_2_772_796` | `1982_3_411_443` | `[1982] 3 S.C.R. 411` | `[1982] 3 S.C.R. 411` |
| `1990_651` | train | `S_1990_2_313_327` | `1966_2_596_606` | `[1966] 59 ITR 718` | `[1966] 2 S.C.R. 596` |
| `1992_137` | validation | `1992_2_109_146` | `1982_2_365_1455` | `[1982] 2 S.C.R. 365` | `[1982] 2 S.C.R. 365` |
| `1992_464` | train | `S_1992_2_62_77` | `S_1963_2_216_234` | `AIR 1963 SC 906` | `[1963] SUPP. 2 S.C.R. 216` |
| `1993_66` | train | `1993_1_891_1026` | `1976_2_347_676` | `[1976] 2 S.C.R. 347` | `[1976] 2 S.C.R. 347` |

The ITR/SCR and AIR/SCR pairs were checked as parallel citations against the
same title-plus-decision-date source. The machine-readable gate values,
source URLs, full query inputs, and source-quality statuses are in
`answer_key/dev_retrieval_probe.json`.

## Step 2 - k=500 ranking-versus-absence diagnostic

| Dev case | Result at k=500 |
| --- | --- |
| `1980_104` | absent at k=500 |
| `1982_186` | absent at k=500 |
| `1984_62` | absent at k=500 |
| `1986_70` | absent at k=500 |
| `1988_238` | absent at k=500 |
| `1990_651` | absent at k=500 |
| `1992_137` | absent at k=500 |
| `1992_464` | absent at k=500 |
| `1993_66` | absent at k=500 |

All nine verified authorities remain absent, so this is not merely a top-100
ranking cutoff. Retrieval used the normal runtime target/near-duplicate and
content self-match exclusions; 2--8 chunks were excluded per query. The full
run IDs, candidate counts, and ranks are in
`artifacts/dev_retrieval_probe_corrected.json`.

## Step 3 - Query construction inspection

Facts-only query inputs range from 844 to 19,973 words (median 5,861), while
the expected-authority chunk medians range from 78 to 105 words (median 90).
The FTS query actually sent to BM25 retains only the first 32 alphanumeric
terms in source order. The exact complete inputs and queries are retained in
the JSON artifact; representative exact FTS queries are:

| Dev case | Facts words | Exact FTS query (32 terms) | Authority median chunk words |
| --- | ---: | --- | ---: |
| `1980_104` | 3,404 | `civil OR appellate OR jurisdiction OR civil OR appeal OR no OR 424 OR of OR 1979 OR appeal OR by OR special OR leave OR from OR the OR judgment OR and OR order OR dated OR 23 OR 1978 OR of OR the OR allahabad OR high OR court OR in OR second OR appeal OR no OR 34 OR 78` | 105 |
| `1984_62` | 9,739 | `civil OR appellate OR jurisdiction OR civil OR appeal OR no OR 3023 OR of OR 1980 OR appeal OR by OR special OR leave OR from OR the OR judgment OR and OR order OR dated OR the OR 21st OR august OR 1980 OR of OR the OR kerala OR high OR court OR in OR no OR 409 OR of` | 88 |
| `1990_651` | 3,039 | `civil OR appellate OR jurisdiction OR civil OR appeal OR no OR 262 OR nc OR of OR 1976 OR from OR the OR judgment OR and OR order OR dated OR 24 OR 1975 OR of OR the OR rajasthan OR high OR court OR in OR civil OR no OR 45 OR of OR 1969 OR mrs OR anjali OR verma` | 78 |
| `1992_464` | 2,871 | `civil OR appellate OR jurisdiction OR civil OR appeal OR no OR 46 OR of OR 1990 OR form OR the OR judgment OR and OR order OR dated OR 89 OR of OR the OR punjab OR and OR haryana OR high OR court OR in OR no OR 3361 OR of OR 1984 OR haksar OR ms OR ritu OR bhalla` | 83 |

This leading-term, boilerplate-heavy composition is a plausible contributing
mechanism for lexical mismatch between facts and authority reasoning. It does
not establish that any specific replacement query strategy will improve
retrieval.

## Steps 4-5 - One-fix rule and freeze decision

No retrieval change was adopted and no alternative was tried. The predeclared
decision rule says that persistent absence for most or all dev cases at k=500
is a lexical-mismatch limitation, not a basis for forcing iterative tuning.
Here the result is 9/9 absent at k=500. The frozen configuration therefore
remains `week7-bm25-diverse-support-v1`: candidate limit 100, full frozen
facts-only input, first-32-term FTS5 OR query, and five-source diverse
selection.

This is an investigated, evidence-backed limitation for the results and
Week 12 error analysis. It bounds retrieval recall and must not be conflated
with citation/grounding correctness for sources that were retrieved.

## Step 6 - fixed-test confirmation policy

No new full 30-case test-split confirmation was run. It is optional and would
not alter this dev-derived freeze decision; the earlier one-time 11-case
confirmation remains preserved in
`artifacts/finalized_test_retrieval_confirmation.json`. The corrected probe
result above is the sole input to the configuration decision.
