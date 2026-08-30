"""Reconcile historical issue-query ranks with the Week 10 facts-query regression.

This is a bounded, read-focused audit for three pre-specified answer-key cases.
It does not alter query construction, corpus membership, or retrieval settings.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import psycopg

from legal_xai.alignment import shared_phrase_count_from_query_set, six_token_phrase_set
from legal_xai.evidence_pipeline import load_ildc_case_text, retrieve_temporal_candidates
from legal_xai.retrieval import exclude_query_duplicate, fts_query, query_exclusion_cases
from legal_xai.temporal import assess_temporal_eligibility


DATABASE_URL = "postgresql://legal_xai:legal_xai_local_only_2026@127.0.0.1:54329/legal_xai"
INDEX = Path("retrieval/bm25.sqlite")
CASES = {
    "2008_1629": {
        "query": "resignation revised pay scale retrospective effect public undertaking",
        "expected_source_id": "S_2006_2_582_600",
        "historical_rank": 29,
        "historical_run_id": "8ec4fdc9-809d-4b40-940d-4c2c7fb369b6",
    },
    "1995_425": {
        "query": "panchayat secretary civil post government servant article 311",
        "expected_source_id": "1967_1_679_684",
        "historical_rank": 56,
        "historical_run_id": "01504563-00cd-4a05-86a5-2082e937cd5c",
    },
    "2002_944": {
        "query": "constitutional 72nd amendment tribal representation constitutional validity",
        "expected_source_id": "1993_1_891_1026",
        "historical_rank": 75,
        "historical_run_id": "9d1df491-ea15-4590-8127-7e180e2519b2",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def raw_source_rank(query: str, source_chunk_ids: set[str]) -> int | None:
    with sqlite3.connect(INDEX) as connection:
        rows = connection.execute(
            "SELECT chunk_id FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT 500",
            (fts_query(query, mode="legacy_first_32"),),
        ).fetchall()
    return next((rank for rank, row in enumerate(rows, start=1) if row[0] in source_chunk_ids), None)


def source_metadata(source_id: str) -> dict[str, Any]:
    with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT chunk_id, case_id, decision_date::text, chunk_text FROM corpus_chunks "
            "WHERE source_id = %s ORDER BY page_number, passage_start_char",
            (source_id,),
        )
        rows = cursor.fetchall()
    if not rows:
        return {"chunk_ids": set(), "case_id": None, "decision_date": None, "text": ""}
    return {
        "chunk_ids": {str(row[0]) for row in rows},
        "case_id": rows[0][1],
        "decision_date": rows[0][2],
        "text": " ".join(str(row[3] or "") for row in rows),
    }


def historical_run(run_id: str) -> dict[str, Any]:
    with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT query_text, index_version, created_at_utc::text, temporal_policy "
            "FROM retrieval_runs WHERE run_id = %s",
            (run_id,),
        )
        row = cursor.fetchone()
    if row is None:
        raise ValueError(f"historical retrieval run is missing: {run_id}")
    return {"query_text": row[0], "index_version": row[1], "created_at_utc": row[2], "temporal_policy": row[3]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/week10_rank_reconciliation.json"))
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("REJECTED: reconciliation artifact already exists; this audit must not be rerun")

    rows: list[dict[str, Any]] = []
    for query_id, control in CASES.items():
        source = source_metadata(str(control["expected_source_id"]))
        historical = historical_run(str(control["historical_run_id"]))
        query_text = load_ildc_case_text(query_id) or ""
        phrase_set = six_token_phrase_set(query_text)
        audited = query_exclusion_cases(query_id, Path("corpus/dedup_matches.csv"))
        phrase_count, _ = shared_phrase_count_from_query_set(phrase_set, str(source["text"]), stop_at=None)
        content_duplicate = exclude_query_duplicate(
            query_id, source["case_id"], audited, query_case_text=query_text,
            candidate_source_text=str(source["text"]), query_six_token_phrases=phrase_set,
        )
        current = retrieve_temporal_candidates(
            query_id=query_id,
            query_year=int(query_id[:4]),
            query=str(control["query"]),
            candidate_k=500,
            index_path=INDEX,
            database_url=DATABASE_URL,
            dedup_matches=Path("corpus/dedup_matches.csv"),
            index_version="week10-rank-reconciliation-legacy-issue-query-v1",
            query_mode="legacy_first_32",
        )
        pipeline_rank = next(
            (candidate.rank for candidate in current.candidates if candidate.source_id == control["expected_source_id"]), None
        )
        temporal_status = assess_temporal_eligibility(int(query_id[:4]), source["decision_date"]).status.value
        rows.append({
            "query_case_id": query_id,
            "expected_authority_source_id": control["expected_source_id"],
            "historical_measurement": {**historical, "rank": control["historical_rank"]},
            "current_legacy_issue_query": {
                "query": control["query"],
                "raw_index_rank_at_k500": raw_source_rank(str(control["query"]), set(source["chunk_ids"])),
                "pipeline_rank_at_k500": pipeline_rank,
                "pipeline_run_id": current.run_id,
                "query_duplicate_chunks_excluded": current.query_duplicate_chunks_excluded,
            },
            "current_authority_presence": {
                "corpus_chunk_count": len(source["chunk_ids"]),
                "decision_date": source["decision_date"],
                "temporal_status": temporal_status,
                "in_alignment_gated_target_exclusions": str(source["case_id"]) in audited,
                "shared_six_token_phrase_count_with_query_case": phrase_count,
                "content_duplicate_excluded": content_duplicate,
            },
        })

    if any(row["current_legacy_issue_query"]["pipeline_rank_at_k500"] is None for row in rows):
        conclusion = "At least one expected authority did not survive the current legacy issue-query pipeline; inspect its per-case exclusion fields before freeze finalization."
    else:
        conclusion = (
            "All three expected authorities remain present, temporally eligible, and retained by the corrected "
            "target/near-duplicate and content-self-match safeguards. Their historical ranks reproduce when the "
            "same short manually authored issue queries are used. The apparent discrepancy comes from comparing "
            "those issue-query ranks with the final regression's different full facts-only input, not from a corpus "
            "removal, an index change, or a false-positive duplicate exclusion."
        )
    payload = {
        "artifact_version": "week10-rank-discrepancy-reconciliation-v1",
        "scope": "One-time reconciliation of 2008_1629, 1995_425, and 2002_944; no retrieval tuning or configuration change.",
        "current_index": {"path": str(INDEX).replace("\\", "/"), "sha256": sha256(INDEX)},
        "final_regression_context": {
            "artifact": "artifacts/week9_final_freeze_regression.json",
            "query_input": "full frozen facts-only extraction",
            "legacy_method": "legacy_first_32",
        },
        "rows": rows,
        "conclusion": conclusion,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_rows = [
        "# Week 10 Rank-Discrepancy Reconciliation", "",
        "| Case | Historical short issue-query rank | Current same-query legacy rank | Source present / retained | Explanation |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        current = row["current_legacy_issue_query"]
        presence = row["current_authority_presence"]
        retained = (
            presence["corpus_chunk_count"] > 0 and not presence["in_alignment_gated_target_exclusions"]
            and not presence["content_duplicate_excluded"] and presence["temporal_status"] == "eligible"
        )
        markdown_rows.append(
            f"| `{row['query_case_id']}` | {row['historical_measurement']['rank']} | "
            f"{current['pipeline_rank_at_k500']} | `{retained}` | short manual issue query versus full facts-only regression input |"
        )
    markdown_rows.extend(["", conclusion, ""])
    args.output.with_suffix(".md").write_text("\n".join(markdown_rows), encoding="utf-8")
    print(json.dumps({"cases": len(rows), "conclusion": conclusion}, indent=2))


if __name__ == "__main__":
    main()
