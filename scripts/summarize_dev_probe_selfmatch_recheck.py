"""Compare the fixed dev probe with its pre-fix salient-term audit artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def rank(record: dict[str, object], depth: str) -> int | None:
    return record["retrievals"][depth]["found_at_rank"]  # type: ignore[index]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, default=Path("artifacts/dev_retrieval_probe_salient_terms.json"))
    parser.add_argument("--after", type=Path, default=Path("artifacts/dev_retrieval_probe_selfmatch_coverage.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/week10_dev_probe_selfmatch_recheck.json"))
    args = parser.parse_args()
    before = {row["query_case_id"]: row for row in json.loads(args.before.read_text(encoding="utf-8"))["results"]}
    after = {row["query_case_id"]: row for row in json.loads(args.after.read_text(encoding="utf-8"))["results"]}
    if set(before) != set(after):
        raise ValueError("Before/after dev-probe case IDs differ")

    rows = []
    for case_id in sorted(after):
        old, new = before[case_id], after[case_id]
        rows.append({
            "query_case_id": case_id,
            "authority_source_id": new["authority_source_id"],
            "before": {depth: rank(old, depth) for depth in ("100", "500")},
            "after": {depth: rank(new, depth) for depth in ("100", "500")},
            "before_duplicate_chunks_excluded": {
                depth: old["retrievals"][depth]["query_duplicate_chunks_excluded"] for depth in ("100", "500")
            },
            "after_duplicate_chunks_excluded": {
                depth: new["retrievals"][depth]["query_duplicate_chunks_excluded"] for depth in ("100", "500")
            },
        })
    count = lambda depth, group: sum(row[group][depth] is not None for row in rows)
    newly_retrieved = [
        row["query_case_id"] for row in rows
        if row["before"]["500"] is None and row["after"]["500"] is not None
    ]
    conclusion = (
        "The pre-fix broad lexical-mismatch conclusion is withdrawn: the self-match rule was a material "
        f"contributor. The corrected configuration retrieves {count('100', 'after')}/9 expected authorities at k=100 "
        f"and {count('500', 'after')}/9 at k=500; newly retrieved after the repair are {', '.join(newly_retrieved)}. "
        "Only the remaining absent cases are residual retrieval failures, not evidence for a corpus-wide lexical-mismatch claim."
    )
    payload = {
        "artifact_version": "week10-dev-probe-selfmatch-recheck-v1",
        "before_artifact": str(args.before).replace("\\", "/"),
        "after_artifact": str(args.after).replace("\\", "/"),
        "configuration": "week10-bm25-salient-terms-selfmatch-coverage-v2",
        "rows": rows,
        "summary": {
            "before_found_at_k100": count("100", "before"),
            "before_found_at_k500": count("500", "before"),
            "after_found_at_k100": count("100", "after"),
            "after_found_at_k500": count("500", "after"),
            "newly_retrieved_after_fix": newly_retrieved,
        },
        "conclusion": conclusion,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Week 10 Dev-Probe Self-Match Recheck", "",
        "| Dev case | Before k=100 / k=500 | After k=100 / k=500 | Result |",
        "| --- | --- | --- | --- |",
    ]
    display = lambda value: f"rank {value}" if value is not None else "absent"
    for row in rows:
        before_display = f"{display(row['before']['100'])} / {display(row['before']['500'])}"
        after_display = f"{display(row['after']['100'])} / {display(row['after']['500'])}"
        result = "newly retrieved" if row["query_case_id"] in newly_retrieved else "unchanged"
        lines.append(f"| `{row['query_case_id']}` | {before_display} | {after_display} | {result} |")
    lines.extend(["", conclusion, ""])
    args.output.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
