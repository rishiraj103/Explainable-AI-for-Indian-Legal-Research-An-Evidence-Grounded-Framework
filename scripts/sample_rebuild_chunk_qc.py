"""Create the fixed 30-chunk manual QC sample after a corpus rebuild."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def records(corpus_root: Path):
    for path in sorted((corpus_root / "ecourts" / "cleaned").glob("year=*/chunks.jsonl")):
        with path.open(encoding="utf-8") as source:
            for line in source:
                yield json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/chunk_qc_rebuild_sample.json"))
    parser.add_argument("--seed", type=int, default=20260828)
    args = parser.parse_args()

    cleaning = json.loads((args.corpus_root / "ecourts" / "cleaning_record.json").read_text(encoding="utf-8"))
    repaired = {
        outcome["source_id"]
        for year in cleaning["years"]
        for outcome in year.get("repair_outcomes", [])
        if outcome["status"] == "included"
    }
    chosen: dict[str, dict[str, object]] = {}
    reservoir: list[dict[str, object]] = []
    rng = random.Random(args.seed)
    seen = 0
    for record in records(args.corpus_root):
        if record["source_id"] in repaired and record["source_id"] not in chosen and len(record["text"].split()) >= 20:
            chosen[record["source_id"]] = record
            continue
        if record["source_id"] in repaired:
            continue
        seen += 1
        random_target = 30 - len(repaired)
        if len(reservoir) < random_target:
            reservoir.append(record)
        else:
            replacement = rng.randrange(seen)
            if replacement < len(reservoir):
                reservoir[replacement] = record
    sample = list(chosen.values()) + reservoir
    if len(sample) != 30:
        raise RuntimeError(f"Expected 30 chunks (one per repaired source plus random passing chunks), found {len(sample)}")
    output = {
        "purpose": "Week 3 manual QC repeated after the quality-gated OCR repair",
        "seed": args.seed,
        "repaired_source_chunks": len(chosen),
        "random_passing_source_chunks": len(reservoir),
        "chunks": sample,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "chunks": len(sample)}, indent=2))


if __name__ == "__main__":
    main()
