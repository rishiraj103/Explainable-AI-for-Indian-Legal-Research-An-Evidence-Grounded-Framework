# Bounded dev-only retrieval investigation

> **Alignment correction — 2026-08-30.** The retrieval ranks below are preserved as an audit trail, but their former interpretation as a facts-to-authority lexical-mismatch finding is **superseded pending reconstruction**. Manual side-by-side reads confirmed that 3 of the original 8 dev probes (37.5%) joined an ILDC text to a different eCourts query judgment through canonical-ID matching. This triggered a full read-only audit of the 30 evaluation answer-key query-source mappings: 20 passed direct content alignment, 9 had a resolved but content-mismatched source, and 1 could not be resolved. See `artifacts/answer_key_alignment_audit.md`. No retrieval setting, answer-key entry, or evaluation result was silently changed.

**Purpose.** This is a pre-freeze diagnostic, not evaluation tuning. The probe population is the eight independently source-verified ILDC **train** cases in `answer_key/dev_retrieval_probe.json`; it is structurally separate from `answer_key/authority_answer_key.json`. The probe validator confirmed that none is in the fixed ILDC test split and neither a query nor authority is one of the permanently excluded low-quality eCourts PDFs.

## Step 1 — ranking versus corpus absence

The current BM25 configuration was run at candidate limits 100 and 500. The verified authority source was absent in every case at both limits.

| Dev case | Expected authority source | Top-100 result | Top-500 result |
| --- | --- | --- | --- |
| `2014_170` | `1994_2_208_238` | absent | absent |
| `2010_721` | `1960_3_388_397` | absent | absent |
| `2008_1460` | `1960_3_388_397` | absent | absent |
| `2008_188` | `S_1997_6_500_512` | absent | absent |
| `2007_946` | `2005_2_1207_1232` | absent | absent |
| `2005_208` | `S_1959_2_406_447` | absent | absent |
| `2004_139` | `2003_1_634_652` | absent | absent |
| `2003_78` | `1971_1_844_850` | absent | absent |

The full machine-readable run IDs, exact ranks, and source metadata are in `artifacts/dev_retrieval_probe_baseline.json`. They cannot support an RQ1 retrieval-recall conclusion until the dev probe is rebuilt with a content-alignment gate.

## Step 2 — query construction inspection

For the probe, the input is the complete shared frozen facts-only extraction (`ildc-predecision-facts-v1`). The current `fts_query` then sends only the first 32 alphanumeric terms, in their original order, as an OR query to FTS5. The full exact facts input and exact FTS query for every case are retained in the JSON artifact above.

| Dev case | Facts input words | Exact FTS terms (32, source order) | Median authority-chunk words |
| --- | ---: | --- | ---: |
| `2014_170` | 3,125 | `thakur OR leave OR granted OR these OR appeals OR are OR directed OR against OR an OR order OR dated OR 9th OR march OR 2007 OR passed OR by OR the OR high OR court OR of OR judicature OR andhra OR pradesh OR at OR hyderabad OR whereby OR the OR high OR court OR has OR set OR aside` | 112 |
| `2010_721` | 1,867 | `markandey OR katju OR leave OR granted OR heard OR learned OR companynsel OR for OR the OR appellant OR none OR has OR appeared OR for OR the OR respondent OR although OR she OR has OR been OR served OR numberice OR we OR had OR earlier OR requested OR mr OR jayant OR bhushan OR learned OR senior OR companynsel` | 75 |
| `2008_1460` | 961 | `altamas OR kabir OR leave OR granted OR the OR question OR whether OR first OR information OR report OR under OR sections OR 420 OR 468 OR 471 OR 34 OR 120 OR ipc OR can OR be OR quashed OR either OR under OR section OR 482 OR of OR the OR code OR of OR criminal OR procedure OR or` | 75 |
| `2008_188` | 2,803 | `civil OR appeal OR no OR 598 OR of OR 2007 OR mathur OR this OR appeal OR is OR directed OR against OR the OR order OR dated OR 12 OR 2006 OR passed OR by OR the OR learned OR single OR judge OR of OR the OR kerala OR high OR court OR whereby OR the OR learned OR single` | 87 |
| `2007_946` | 1,332 | `arising OR out OR of OR no OR 3358 OR of OR 2007 OR heard OR learned OR companynsel OR for OR the OR parties OR leave OR granted OR this OR appeal OR by OR special OR leave OR is OR directed OR against OR the OR judgment OR and OR order OR dated OR 17th OR february OR 2006 OR passed` | 95 |
| `2005_208` | 1,969 | `santosh OR hegde OR noticing OR certain OR companytradictory OR views OR in OR three OR different OR judgments OR of OR this OR court OR in OR teg OR singh OR vs OR charan OR singh OR 1977 OR scc OR 732 OR kesar OR singh OR vs OR sadhu OR 1996 OR scc OR 711 OR and OR balwant OR singh` | 97 |
| `2004_139` | 943 | `with OR criminal OR appeal OR no OR 227 OR of OR 1997 OR sabharwal OR these OR appeals OR by OR special OR leave OR challenge OR the OR judgment OR of OR the OR high OR court OR by OR which OR the OR companyviction OR of OR the OR appellants OR for OR offence OR under OR section OR 201` | 78 |
| `2003_78` | 3,460 | `arijit OR pasayat OR the OR only OR point OR involved OR in OR this OR appeal OR is OR whether OR the OR appellants OR termination OR from OR service OR is OR in OR order OR factual OR scenario OR which OR is OR almost OR undisputed OR is OR as OR follows OR the OR appellant OR was OR appointed` | 76 |

Facts slices range from 943–3,460 words (median 1,918), compared with authority chunks of 75–112 words (median 82.5). The leading-term construction is plausibly diffuse and boilerplate-heavy. However, it would be invalid to claim that a replacement fixes the problem without a positive dev result.

## Steps 3–5 — one-fix rule and freeze decision

**Provisional path, superseded by alignment correction.** No salient-term extractor or BM25 parameter modification was attempted, and `config/evidence_selection.json` remains unchanged at `week7-bm25-diverse-support-v1`, candidate limit 100, and five-source selection. The original 8/8 top-500 absence cannot be used to diagnose lexical mismatch because the expected-authority mappings were not all aligned to the ILDC inputs.

The original before/final comparison remains preserved (0/8 authorities in top-100), but it is not a valid retrieval-quality result. The configuration remains unchanged until the approved matching-logic correction, permanent alignment gate, and rebuilt dev-only investigation are complete.

## Step 6 — one-time fixed-test confirmation

After the decision above, the finalized unchanged configuration was run once on the eleven specified fixed-test answer-key cases using their already-recorded issue queries. The results were not used to tune any setting; details and run IDs are in `artifacts/finalized_test_retrieval_confirmation.json`.

| Result | Cases |
| --- | --- |
| Retrieved and selected | `1995_412` (22), `1986_397` (2) |
| Retrieved but not selected | `2008_1629` (29), `1995_425` (56), `2002_944` (75), `1988_96` (96) |
| Absent at top-100 | `1995_403`, `1982_29`, `1994_632`, `1985_40`, `1992_84` |

The confirmation matches the previously recorded pattern except that `2008_1629` is now explicitly listed as retrieved-but-not-selected at rank 29. This remains a deferred Week 12 evidence-selection analysis example; it did not affect the pre-freeze decision.
