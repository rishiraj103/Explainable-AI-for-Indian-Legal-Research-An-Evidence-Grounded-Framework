"""Retrieve BM25 evidence, enforce temporal eligibility, and log every rank."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from legal_xai.temporal import assess_temporal_eligibility
from legal_xai.retrieval import exclude_query_duplicate, fts_query, query_exclusion_cases
from build_bm25_index import INDEX_VERSION
from load_provenance import DEFAULT_DATABASE_URL


TEMPORAL_POLICY = "precedent_decision_year < ildc_query_year; same-year excluded as ambiguous"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--query-year", type=int, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--candidate-k", type=int, default=100)
    parser.add_argument("--index", type=Path, default=Path("retrieval/bm25.sqlite"))
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--output", type=Path, default=Path("artifacts/retrieval_result.json"))
    parser.add_argument("--dedup-matches", type=Path, default=Path("corpus/dedup_matches.csv"))
    args = parser.parse_args()
    if args.top_k < 1 or args.candidate_k < args.top_k:
        raise ValueError("candidate-k must be at least top-k, and both must be positive")

    audited_near_cases = query_exclusion_cases(args.query_id, args.dedup_matches)
    with sqlite3.connect(args.index) as index:
        rows = index.execute(
            "SELECT chunk_id, bm25(chunks_fts) AS raw_score "
            "FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY raw_score LIMIT ?",
            (fts_query(args.query), args.candidate_k),
        ).fetchall()
    if not rows:
        raise ValueError("BM25 returned no candidates for the supplied query")

    chunk_ids = [row[0] for row in rows]
    with psycopg.connect(args.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT chunk_id, source_id, case_id, citation, decision_date, court, pdf_file, page_number, "
                "passage_start_char, passage_end_char, chunk_text "
                "FROM corpus_chunks WHERE chunk_id = ANY(%s)",
                (chunk_ids,),
            )
            metadata = {row[0]: row for row in cursor.fetchall()}

            run_id = uuid.uuid4()
            ranked: list[dict[str, object]] = []
            duplicate_excluded = 0
            for rank, (chunk_id, raw_score) in enumerate(rows, start=1):
                row = metadata[chunk_id]
                if exclude_query_duplicate(args.query_id, row[2], audited_near_cases):
                    duplicate_excluded += 1
                    continue
                decision = assess_temporal_eligibility(args.query_year, row[4])
                ranked.append({
                    "rank": rank,
                    "chunk_id": chunk_id,
                    "source_id": row[1],
                    "case_id": row[2],
                    "citation": row[3],
                    "decision_date": row[4].isoformat(),
                    "court": row[5],
                    "pdf_file": row[6],
                    "page_number": row[7],
                    "passage_start_char": row[8],
                    "passage_end_char": row[9],
                    "bm25_score": -float(raw_score),
                    "temporal_status": decision.status.value,
                    "text": row[10],
                })

            cursor.execute(
                "INSERT INTO retrieval_runs (run_id, query_id, query_year, query_text, index_version, "
                "created_at_utc, temporal_policy) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (run_id, args.query_id, args.query_year, args.query, INDEX_VERSION, datetime.now(UTC), TEMPORAL_POLICY),
            )
            cursor.executemany(
                "INSERT INTO retrieval_results (run_id, rank, chunk_id, bm25_score, temporal_status) "
                "VALUES (%s, %s, %s, %s, %s)",
                [
                    (run_id, item["rank"], item["chunk_id"], item["bm25_score"], item["temporal_status"])
                    for item in ranked
                ],
            )
        connection.commit()

    eligible = [item for item in ranked if item["temporal_status"] == "eligible"][:args.top_k]
    result = {
        "run_id": str(run_id),
        "query_id": args.query_id,
        "query_year": args.query_year,
        "query": args.query,
        "candidate_count": len(ranked),
        "query_duplicate_chunks_excluded": duplicate_excluded,
        "eligible_returned": len(eligible),
        "status_counts": {
            status: sum(item["temporal_status"] == status for item in ranked)
            for status in ("eligible", "ambiguous_excluded", "ineligible", "excluded_missing_metadata")
        },
        "eligible_results": eligible,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "eligible_results"}, indent=2))


if __name__ == "__main__":
    main()
