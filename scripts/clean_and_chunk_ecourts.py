"""Extract, clean, and label locally acquired eCourts PDFs.

This creates a JSONL evidence-preparation artifact only; it does not create a
retrieval index.  Each output record retains the case metadata and a PDF-page
locator.  Raw PDFs remain unchanged under corpus/ecourts/pdfs/.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pymupdf

from legal_xai.corpus import (
    chunk_page_text,
    clean_page_text,
    is_non_evidentiary_chunk,
    repeated_page_furniture,
)


METADATA_FIELDS = [
    "case_id", "citation", "title", "petitioner", "respondent", "decision_date",
    "court", "disposal_nature", "path", "year",
]


def load_metadata(corpus_root: Path, metadata_year: int, cache: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Load metadata by its source year, retaining the stable source `path`."""

    if metadata_year not in cache:
        metadata_path = corpus_root / "ecourts" / "metadata" / f"year={metadata_year}" / "metadata.parquet"
        cache[metadata_year] = pd.read_parquet(metadata_path, columns=METADATA_FIELDS).set_index("path")
    return cache[metadata_year]


def process_year(
    corpus_root: Path,
    year: int,
    max_words: int,
    max_sentences: int,
    metadata_cache: dict[int, pd.DataFrame],
) -> dict[str, int]:
    pdf_dir = corpus_root / "ecourts" / "pdfs" / f"year={year}"
    output_dir = corpus_root / "ecourts" / "cleaned" / f"year={year}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "chunks.jsonl"

    if not pdf_dir.exists():
        return {"year": year, "documents": 0, "chunks": 0, "missing_metadata": 0}

    documents = chunks = missing_metadata = excluded_non_evidentiary_chunks = 0
    with output_path.open("w", encoding="utf-8") as output:
        for pdf_path in sorted(pdf_dir.glob("*_EN.pdf")):
            source_path = pdf_path.stem.removesuffix("_EN")
            metadata_year = int(source_path[:4]) if source_path[:4].isdigit() else year
            metadata = load_metadata(corpus_root, metadata_year, metadata_cache)
            if source_path not in metadata.index:
                missing_metadata += 1
                continue
            row = metadata.loc[source_path]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            documents += 1
            with pymupdf.open(pdf_path) as document:
                raw_pages = [page.get_text("text") for page in document]
                repeated_furniture = repeated_page_furniture(raw_pages)
                for page_index, raw_page in enumerate(raw_pages, start=1):
                    cleaned = clean_page_text(raw_page, repeated_furniture)
                    for chunk in chunk_page_text(
                        cleaned, page_index, max_words=max_words, max_sentences=max_sentences
                    ):
                        if is_non_evidentiary_chunk(chunk.text):
                            excluded_non_evidentiary_chunks += 1
                            continue
                        record = {
                            field: (None if pd.isna(row[field]) else str(row[field]))
                            for field in METADATA_FIELDS if field != "path"
                        }
                        record["path"] = source_path
                        record.update({
                            "source_id": source_path,
                            "chunk_id": f"{source_path}::p{chunk.page_number:04d}::c{chunk.chunk_number:03d}",
                            "pdf_file": pdf_path.name,
                            "page_number": chunk.page_number,
                            "passage_start_char": chunk.start_char,
                            "passage_end_char": chunk.end_char,
                            "text": chunk.text,
                            "cleaning_version": "v1-conservative-page-text",
                        })
                        output.write(json.dumps(record, ensure_ascii=False) + "\n")
                        chunks += 1
    return {
        "year": year,
        "documents": documents,
        "chunks": chunks,
        "missing_metadata": missing_metadata,
        "excluded_non_evidentiary_chunks": excluded_non_evidentiary_chunks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2020)
    parser.add_argument("--max-words", type=int, default=220)
    parser.add_argument("--max-sentences", type=int, default=4)
    args = parser.parse_args()

    metadata_cache: dict[int, pd.DataFrame] = {}
    results = [process_year(args.corpus_root, year, args.max_words, args.max_sentences, metadata_cache)
               for year in range(args.start_year, args.end_year + 1)]
    record = {
        "updated_at_utc": datetime.now(UTC).isoformat(),
        "cleaning_version": "v1-conservative-page-text",
        "chunking": {"max_words": args.max_words, "max_sentences": args.max_sentences},
        "years": results,
    }
    output = args.corpus_root / "ecourts" / "cleaning_record.json"
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
