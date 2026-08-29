"""Run E3 retrieval, evidence selection, controlled answer rendering, and grounding audit."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from build_bm25_index import INDEX_VERSION
from load_provenance import DEFAULT_DATABASE_URL
from legal_xai.evidence_pipeline import retrieve_temporal_candidates, select_diverse_evidence
from legal_xai.grounded_answer import ANSWER_VERSION, assert_answer_grounded, render_grounded_answer


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
        index_version=INDEX_VERSION,
    )
    selected = select_diverse_evidence(retrieved.candidates, int(selection_config["max_selected_evidence"]))
    answer = render_grounded_answer(query=args.query, selected_evidence=selected).as_dict()
    assert_answer_grounded(answer, selected)
    result = {
        "experiment": answer_config["experiment"],
        "selection_version": selection_config["selection_version"],
        "run_id": retrieved.run_id,
        "query_id": retrieved.query_id,
        "query_year": retrieved.query_year,
        "candidate_count": len(retrieved.candidates),
        "selected_evidence_count": len(selected),
        "query_duplicate_chunks_excluded": retrieved.query_duplicate_chunks_excluded,
        "status_counts": retrieved.status_counts,
        "grounding_audit": "passed",
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
