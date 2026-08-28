"""Run Week 7 retrieval plus deterministic evidence selection for one query."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from build_bm25_index import INDEX_VERSION
from legal_xai.evidence_pipeline import retrieve_temporal_candidates, select_diverse_evidence
from load_provenance import DEFAULT_DATABASE_URL


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--query-year", type=int, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--config", type=Path, default=Path("config/evidence_selection.json"))
    parser.add_argument("--index", type=Path, default=Path("retrieval/bm25.sqlite"))
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--dedup-matches", type=Path, default=Path("corpus/dedup_matches.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/evidence_pipeline_result.json"))
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    retrieved = retrieve_temporal_candidates(
        query_id=args.query_id, query_year=args.query_year, query=args.query,
        candidate_k=int(config["candidate_k"]), index_path=args.index, database_url=args.database_url,
        dedup_matches=args.dedup_matches, index_version=INDEX_VERSION,
    )
    selected = select_diverse_evidence(retrieved.candidates, int(config["max_selected_evidence"]))
    result = {
        "selection_version": config["selection_version"],
        "run_id": retrieved.run_id,
        "query_id": retrieved.query_id,
        "query_year": retrieved.query_year,
        "query": retrieved.query,
        "candidate_count": len(retrieved.candidates),
        "query_duplicate_chunks_excluded": retrieved.query_duplicate_chunks_excluded,
        "status_counts": retrieved.status_counts,
        "selected_evidence": [candidate.as_dict() for candidate in selected],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "run_id": result["run_id"], "selected_evidence": len(selected),
        "selection_version": result["selection_version"],
    }, indent=2))


if __name__ == "__main__":
    main()
