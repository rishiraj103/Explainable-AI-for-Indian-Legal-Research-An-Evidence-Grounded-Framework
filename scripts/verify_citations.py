"""Verify a persisted E3 answer's citations against corpus and retrieval provenance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg

from load_provenance import DEFAULT_DATABASE_URL
from legal_xai.citation_verifier import (
    CorpusEvidenceRecord,
    VERIFICATION_VERSION,
    evaluate_against_answer_key,
    verify_answer_citations,
)
from legal_xai.retrieval import query_exclusion_cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Persisted run_grounded_answer_pipeline JSON")
    parser.add_argument("--output", type=Path, default=Path("artifacts/citation_verification_result.json"))
    parser.add_argument("--config", type=Path, default=Path("config/citation_verification.json"))
    parser.add_argument("--answer-key", type=Path, default=Path("answer_key/authority_answer_key.json"))
    parser.add_argument("--dedup-matches", type=Path, default=Path("corpus/dedup_matches.csv"))
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config["verification_version"] != VERIFICATION_VERSION:
        raise ValueError("Citation-verification configuration does not match verifier version")
    run = json.loads(args.input.read_text(encoding="utf-8"))
    evidence = run["answer"].get("evidence", [])
    chunk_ids = [item["chunk_id"] for item in evidence]
    records: dict[str, CorpusEvidenceRecord] = {}
    retrieved_chunk_ids: set[str] = set()
    with psycopg.connect(args.database_url) as connection:
        with connection.cursor() as cursor:
            if chunk_ids:
                cursor.execute(
                    "SELECT chunk_id, source_id, case_id, citation, decision_date, court, pdf_file, "
                    "page_number, passage_start_char, passage_end_char, chunk_text "
                    "FROM corpus_chunks WHERE chunk_id = ANY(%s)",
                    (chunk_ids,),
                )
                records = {
                    row[0]: CorpusEvidenceRecord(
                        chunk_id=row[0], source_id=row[1], case_id=row[2], citation=row[3],
                        decision_date=row[4].isoformat(), court=row[5], pdf_file=row[6],
                        page_number=row[7], passage_start_char=row[8], passage_end_char=row[9], text=row[10],
                    )
                    for row in cursor.fetchall()
                }
            cursor.execute("SELECT chunk_id FROM retrieval_results WHERE run_id = %s", (run["run_id"],))
            retrieved_chunk_ids = {row[0] for row in cursor.fetchall()}

    checks = verify_answer_citations(
        answer=run["answer"], query_id=run["query_id"], query_year=int(run["query_year"]),
        corpus_records=records, retrieved_chunk_ids=retrieved_chunk_ids,
        audited_near_case_ids=query_exclusion_cases(run["query_id"], args.dedup_matches),
    )
    key = json.loads(args.answer_key.read_text(encoding="utf-8"))
    answer_key_measurement = evaluate_against_answer_key(
        query_id=run["query_id"], checks=checks, answer_key_entries=key["entries"],
    )
    output = {
        "verification_version": VERIFICATION_VERSION,
        "input": str(args.input),
        "run_id": run["run_id"],
        "query_id": run["query_id"],
        "query_year": run["query_year"],
        "citation_count": len(checks),
        "passed_count": sum(check.passed for check in checks),
        "failed_count": sum(not check.passed for check in checks),
        "checks": [check.as_dict() for check in checks],
        "answer_key_measurement": answer_key_measurement,
        "status": "passed" if all(check.passed for check in checks) else "failed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: output[key] for key in ("citation_count", "passed_count", "failed_count", "status")}, indent=2))


if __name__ == "__main__":
    main()
