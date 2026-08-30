"""Run the bounded Week 10 E4 replay twice and compare stable output content."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUERY = {"query_id": "week10-replay-01", "query_year": 2020, "query": "anticipatory bail section 438"}


def stable_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove the database run UUID while retaining all reproducibility-relevant data."""
    result = dict(payload)
    result.pop("run_id", None)
    return result


def digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_once(label: str) -> dict[str, Any]:
    output = ROOT / "artifacts" / f"week10_replay_{label}.json"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    command = [
        sys.executable, "scripts/run_grounded_answer_pipeline.py",
        "--query-id", QUERY["query_id"], "--query-year", str(QUERY["query_year"]),
        "--query", QUERY["query"], "--output", str(output),
    ]
    subprocess.run(command, cwd=ROOT, env=environment, check=True, capture_output=True, text=True)
    return json.loads(output.read_text(encoding="utf-8"))


def main() -> None:
    first = run_once("first")
    second = run_once("second")
    first_stable = stable_result(first)
    second_stable = stable_result(second)
    matches = first_stable == second_stable
    result = {
        "replay_version": "week10-bounded-e4-replay-v1",
        "query": QUERY,
        "first_run_id": first["run_id"],
        "second_run_id": second["run_id"],
        "comparison_excludes": ["run_id"],
        "first_stable_sha256": digest(first_stable),
        "second_stable_sha256": digest(second_stable),
        "matches": matches,
        "selected_chunk_ids": [item["chunk_id"] for item in first["answer"]["supporting_evidence"]],
        "citation_verification": first["citation_verification"],
        "temporal_status_counts": first["status_counts"],
    }
    output = ROOT / "artifacts/week10_reproducibility_replay.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not matches:
        raise SystemExit("Week 10 replay did not reproduce its stable E4 output")
    print(json.dumps({key: result[key] for key in ("matches", "first_stable_sha256", "selected_chunk_ids")}, indent=2))


if __name__ == "__main__":
    main()
