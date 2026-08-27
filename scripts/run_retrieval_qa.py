"""Run the fixed Week 4 retrieval relevance query set."""

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
    parser.add_argument("--queries", type=Path, default=Path("config/retrieval_qa_queries.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/retrieval_qa_results.json"))
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    retrieve_script = Path(__file__).with_name("retrieve_evidence.py")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")
    results = []
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary = Path(temporary_directory)
        for query in json.loads(args.queries.read_text(encoding="utf-8")):
            result_path = temporary / f"{query['query_id']}.json"
            subprocess.run(
                [
                    sys.executable, str(retrieve_script), "--query-id", query["query_id"],
                    "--query-year", str(query["query_year"]), "--query", query["query"],
                    "--top-k", "3", "--candidate-k", "30", "--output", str(result_path),
                ],
                cwd=project_root,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            results.append(json.loads(result_path.read_text(encoding="utf-8")))
    output = {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "query_count": len(results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"query_count": len(results), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
