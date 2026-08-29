"""Run a reproducible retrieval probe using only dev-only verified authorities.

This diagnostic never reads the evaluation answer key.  It takes each ILDC
train/validation probe through the frozen facts extractor, records the exact
FTS query, and reports whether its independently verified authority appears.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

import psycopg
import pyarrow.parquet as pq

from legal_xai.evidence_pipeline import retrieve_temporal_candidates
from legal_xai.facts import extract_case_facts, load_facts_extraction_rule
from legal_xai.retrieval import fts_query


DATABASE_URL = "postgresql://legal_xai:legal_xai_local_only_2026@127.0.0.1:54329/legal_xai"


def load_ildc_texts(probe: dict[str, object]) -> dict[str, str]:
    wanted = {str(entry["query_case_id"]) for entry in probe["entries"]}
    texts: dict[str, str] = {}
    for split in ("train", "validation"):
        table = pq.read_table(
            f"corpus/ildc/single_{split}.parquet",
            columns=["id", "text"],
            filters=[("id", "in", sorted(wanted))],
        )
        for row in table.to_pylist():
            case_id = str(row["id"])
            if case_id in wanted:
                texts[case_id] = str(row["text"] or "")
    if texts.keys() != wanted:
        raise ValueError(f"missing dev probe ILDC text: {sorted(wanted - texts.keys())}")
    return texts


def authority_chunk_statistics(source_id: str) -> dict[str, int]:
    with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT chunk_text FROM corpus_chunks WHERE source_id = %s", (source_id,))
        lengths = [len(str(row[0]).split()) for row in cursor.fetchall()]
    if not lengths:
        raise ValueError(f"authority source is absent from provenance: {source_id}")
    return {
        "authority_chunk_count": len(lengths),
        "authority_chunk_median_words": int(statistics.median(lengths)),
        "authority_chunk_max_words": max(lengths),
    }


def found_rank(retrieval: object, authority_source_id: str) -> int | None:
    for candidate in retrieval.candidates:
        if candidate.source_id == authority_source_id:
            return candidate.rank
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, default=Path("answer_key/dev_retrieval_probe.json"))
    parser.add_argument("--candidate-k", type=int, action="append", default=[100, 500])
    parser.add_argument("--index-version", default="week9-bm25-diverse-support-v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    probe = json.loads(args.probe.read_text(encoding="utf-8"))
    if any(entry.get("split") != "dev" for entry in probe["entries"]):
        raise ValueError("probe contains non-dev entry")
    texts = load_ildc_texts(probe)
    rule = load_facts_extraction_rule("config/facts_extraction.json")
    results: list[dict[str, object]] = []
    for entry in probe["entries"]:
        case_id = str(entry["query_case_id"])
        facts = extract_case_facts(texts[case_id], rule)
        query = facts.text
        query_year = int(str(entry["query_decision_date"])[:4])
        retrievals: dict[str, object] = {}
        for candidate_k in sorted(set(args.candidate_k)):
            retrieval = retrieve_temporal_candidates(
                query_id=case_id,
                query_year=query_year,
                query=query,
                candidate_k=candidate_k,
                index_path=Path("retrieval/bm25.sqlite"),
                database_url=DATABASE_URL,
                dedup_matches=Path("corpus/dedup_matches.csv"),
                index_version=args.index_version,
            )
            rank = found_rank(retrieval, str(entry["authority_source_id"]))
            retrievals[str(candidate_k)] = {
                "run_id": retrieval.run_id,
                "found_at_rank": rank,
                "result": f"rank_{rank}" if rank is not None else f"absent_at_k_{candidate_k}",
                "candidate_count_after_filters": len(retrieval.candidates),
                "query_duplicate_chunks_excluded": retrieval.query_duplicate_chunks_excluded,
            }
        results.append({
            "query_case_id": case_id,
            "source_split": entry["source_split"],
            "authority_source_id": entry["authority_source_id"],
            "query_extraction_boundary_reason": facts.boundary_reason,
            "query_input": query,
            "query_input_word_count": len(query.split()),
            "bm25_fts_query": fts_query(query),
            "bm25_fts_term_count": len(fts_query(query).split(" OR ")),
            **authority_chunk_statistics(str(entry["authority_source_id"])),
            "retrievals": retrievals,
        })
    payload = {
        "artifact_version": "dev-retrieval-probe-baseline-v1",
        "probe_file": str(args.probe).replace("\\", "/"),
        "query_construction": "full frozen facts-only input; current fts_query then keeps the first 32 alphanumeric terms in source order",
        "candidate_ks": sorted(set(args.candidate_k)),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(results)} dev-only probe results to {args.output}")


if __name__ == "__main__":
    main()
