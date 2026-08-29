"""Run the fixed Week 8 E3 answer-grounding QA query set."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=Path("config/week8_grounded_answer_queries.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/week8_grounded_answer_qa.json"))
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    runner = Path(__file__).with_name("run_grounded_answer_pipeline.py")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")
    results = []
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary = Path(temporary_directory)
        for query in json.loads(args.queries.read_text(encoding="utf-8")):
            result_path = temporary / f"{query['query_id']}.json"
            subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--query-id",
                    query["query_id"],
                    "--query-year",
                    str(query["query_year"]),
                    "--query",
                    query["query"],
                    "--output",
                    str(result_path),
                ],
                cwd=project_root,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            results.append(json.loads(result_path.read_text(encoding="utf-8")))
    if any(result["grounding_audit"] != "passed" for result in results):
        raise ValueError("A Week 8 grounding audit failed")
    output = {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "answer_version": "week8-controlled-evidence-renderer-v1",
        "query_count": len(results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"query_count": len(results), "grounding_audit": "passed"}, indent=2))


if __name__ == "__main__":
    main()
