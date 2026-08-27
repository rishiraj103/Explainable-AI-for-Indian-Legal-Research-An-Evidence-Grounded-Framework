"""Verify that the locally prepared eCourts corpus is complete and traceable.

This validator does not build a retrieval index. It reconciles public-source
file counts, local PDFs, metadata rows, and the local clean-chunk JSONL output.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


REQUIRED_CHUNK_FIELDS = (
    "chunk_id",
    "source_id",
    "citation",
    "decision_date",
    "court",
    "path",
    "pdf_file",
    "page_number",
    "passage_start_char",
    "passage_end_char",
    "text",
)


def verify_year(corpus_root: Path, year: int, expected_pdf_count: int) -> dict[str, object]:
    root = corpus_root / "ecourts"
    pdf_dir = root / "pdfs" / f"year={year}"
    metadata_path = root / "metadata" / f"year={year}" / "metadata.parquet"
    chunks_path = root / "cleaned" / f"year={year}" / "chunks.jsonl"

    local_pdfs = {path.name for path in pdf_dir.glob("*_EN.pdf")} if pdf_dir.exists() else set()
    metadata_rows = len(pd.read_parquet(metadata_path, columns=["path"])) if metadata_path.exists() else 0
    documents_with_chunks: set[str] = set()
    chunks = malformed_json = invalid_records = invalid_bounds = 0

    if chunks_path.exists():
        with chunks_path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    malformed_json += 1
                    continue
                chunks += 1
                if any(record.get(field) in (None, "") for field in REQUIRED_CHUNK_FIELDS):
                    invalid_records += 1
                    continue
                start, end = record["passage_start_char"], record["passage_end_char"]
                if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                    invalid_bounds += 1
                documents_with_chunks.add(record["pdf_file"])

    return {
        "year": year,
        "expected_pdfs": expected_pdf_count,
        "local_pdfs": len(local_pdfs),
        "metadata_rows": metadata_rows,
        "chunks": chunks,
        "documents_with_chunks": len(documents_with_chunks),
        "pdfs_without_chunks": sorted(local_pdfs - documents_with_chunks),
        "chunk_references_without_local_pdf": sorted(documents_with_chunks - local_pdfs),
        "malformed_json_records": malformed_json,
        "records_missing_required_fields": invalid_records,
        "records_with_invalid_bounds": invalid_bounds,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2020)
    parser.add_argument("--output", type=Path, default=Path("artifacts/corpus_readiness.json"))
    args = parser.parse_args()

    acquisition = json.loads((args.corpus_root / "ecourts" / "acquisition_record.json").read_text(encoding="utf-8"))
    expected = {entry["year"]: entry["source_file_count"] for entry in acquisition["years"]}
    years = [verify_year(args.corpus_root, year, expected[year]) for year in range(args.start_year, args.end_year + 1)]
    totals = {
        key: sum(int(year[key]) for year in years)
        for key in ("expected_pdfs", "local_pdfs", "metadata_rows", "chunks", "documents_with_chunks",
                    "malformed_json_records", "records_missing_required_fields", "records_with_invalid_bounds")
    }
    totals["pdfs_without_chunks"] = sum(len(year["pdfs_without_chunks"]) for year in years)
    totals["chunk_references_without_local_pdf"] = sum(
        len(year["chunk_references_without_local_pdf"]) for year in years
    )
    ready = (
        all(year["expected_pdfs"] == year["local_pdfs"] for year in years)
        and totals["pdfs_without_chunks"] == 0
        and totals["chunk_references_without_local_pdf"] == 0
        and totals["malformed_json_records"] == 0
        and totals["records_missing_required_fields"] == 0
        and totals["records_with_invalid_bounds"] == 0
    )
    result = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "scope": {"years": [args.start_year, args.end_year], "retrieval_index_built": False},
        "ready_for_week_4_retrieval_indexing": ready,
        "totals": totals,
        "years": years,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"ready": ready, "totals": totals}, indent=2))


if __name__ == "__main__":
    main()
