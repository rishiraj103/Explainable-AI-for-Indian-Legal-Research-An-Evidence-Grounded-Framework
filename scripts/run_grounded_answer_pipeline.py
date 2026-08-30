"""Run E4 retrieval, evidence selection, controlled explanation rendering, and grounding audit."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from build_bm25_index import INDEX_VERSION
from load_provenance import DEFAULT_DATABASE_URL
from legal_xai.citation_verifier import CorpusEvidenceRecord, verify_answer_citations
from legal_xai.evidence_pipeline import retrieve_temporal_candidates, select_diverse_evidence
from legal_xai.grounded_answer import ANSWER_VERSION, assert_answer_grounded, render_grounded_answer
from legal_xai.retrieval import query_exclusion_cases


def verify_rendered_explanation(*, answer: dict, run_id: str, query_id: str, query_year: int,
                                database_url: str, dedup_matches: Path) -> list[dict]:
    """Run the Week 9 citation contract inside the Week 10 E4 execution path."""
    selected_chunk_ids = [item["chunk_id"] for item in answer["supporting_evidence"]]
    records: dict[str, CorpusEvidenceRecord] = {}
    retrieved_chunk_ids: set[str] = set()
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            if selected_chunk_ids:
                cursor.execute(
                    "SELECT chunk_id, source_id, case_id, citation, decision_date, title, court, pdf_file, "
                    "page_number, passage_start_char, passage_end_char, chunk_text "
                    "FROM corpus_chunks WHERE chunk_id = ANY(%s)",
                    (selected_chunk_ids,),
                )
                records = {
                    row[0]: CorpusEvidenceRecord(
                        chunk_id=row[0], source_id=row[1], case_id=row[2], citation=row[3],
                        decision_date=row[4].isoformat(), title=row[5], court=row[6], pdf_file=row[7],
                        page_number=row[8], passage_start_char=row[9], passage_end_char=row[10], text=row[11],
                    )
                    for row in cursor.fetchall()
                }
            cursor.execute(
                "SELECT chunk_id FROM retrieval_results WHERE run_id = %s AND temporal_status = 'eligible'",
                (run_id,),
            )
            retrieved_chunk_ids = {row[0] for row in cursor.fetchall()}
    checks = verify_answer_citations(
        answer=answer, query_id=query_id, query_year=query_year, corpus_records=records,
        retrieved_chunk_ids=retrieved_chunk_ids,
        audited_near_case_ids=query_exclusion_cases(query_id, dedup_matches),
    )
    failures = [check for check in checks if not check.passed]
    if failures:
        raise ValueError(f"E4 citation/temporal verification failed: {[check.as_dict() for check in failures]}")
    return [check.as_dict() for check in checks]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--query-year", required=True, type=int)
    parser.add_argument("--query", required=True)
    parser.add_argument("--selection-config", type=Path, default=Path("config/evidence_selection.json"))
    parser.add_argument("--answer-config", type=Path, default=Path("config/grounded_answer.json"))
    parser.add_argument("--index", type=Path, default=Path("retrieval/bm25.sqlite"))
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--dedup-matches", type=Path, default=Path("corpus/dedup_matches.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/grounded_answer_result.json"))
    args = parser.parse_args()

    selection_config = json.loads(args.selection_config.read_text(encoding="utf-8"))
    answer_config = json.loads(args.answer_config.read_text(encoding="utf-8"))
    if answer_config["answer_version"] != ANSWER_VERSION:
        raise ValueError("Grounded-answer configuration does not match the renderer version")
    if answer_config["generation_mode"] != "controlled_extract_only":
        raise ValueError("E3 requires the frozen controlled extract-only renderer")

    retrieved = retrieve_temporal_candidates(
        query_id=args.query_id,
        query_year=args.query_year,
        query=args.query,
        candidate_k=int(selection_config["candidate_k"]),
        index_path=args.index,
        database_url=args.database_url,
        dedup_matches=args.dedup_matches,
        index_version=f"{INDEX_VERSION};{selection_config['selection_version']}",
    )
    selected = select_diverse_evidence(retrieved.candidates, int(selection_config["max_selected_evidence"]))
    answer = render_grounded_answer(query=args.query, selected_evidence=selected).as_dict()
    assert_answer_grounded(answer, selected)
    citation_checks = verify_rendered_explanation(
        answer=answer, run_id=retrieved.run_id, query_id=retrieved.query_id, query_year=retrieved.query_year,
        database_url=args.database_url, dedup_matches=args.dedup_matches,
    )
    result = {
        "experiment": answer_config["experiment"],
        "selection_version": selection_config["selection_version"],
        "query_construction_version": selection_config["query_construction_version"],
        "run_id": retrieved.run_id,
        "query_id": retrieved.query_id,
        "query_year": retrieved.query_year,
        "candidate_count": len(retrieved.candidates),
        "selected_evidence_count": len(selected),
        "query_duplicate_chunks_excluded": retrieved.query_duplicate_chunks_excluded,
        "status_counts": retrieved.status_counts,
        "grounding_audit": "passed",
        "citation_verification": {
            "status": "passed",
            "passed_count": len(citation_checks),
            "checks": citation_checks,
        },
        "answer": answer,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "run_id": result["run_id"],
        "selected_evidence": result["selected_evidence_count"],
        "grounding_audit": result["grounding_audit"],
    }, indent=2))


if __name__ == "__main__":
    main()
