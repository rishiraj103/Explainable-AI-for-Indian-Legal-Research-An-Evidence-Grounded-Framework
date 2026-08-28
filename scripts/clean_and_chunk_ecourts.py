"""Extract, clean, and label locally acquired eCourts PDFs.

This creates a JSONL evidence-preparation artifact only; it does not create a
retrieval index.  Each output record retains the case metadata and a PDF-page
locator.  Raw PDFs remain unchanged under corpus/ecourts/pdfs/.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pymupdf
import pyarrow.parquet as pq

from audit_ecourts_extraction import classify, text_metrics
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


def load_metadata(corpus_root: Path, metadata_year: int, cache: dict[int, dict[str, dict[str, object]]]) -> dict[str, dict[str, object]]:
    """Load metadata by its source year, retaining the stable source `path`."""

    if metadata_year not in cache:
        metadata_path = corpus_root / "ecourts" / "metadata" / f"year={metadata_year}" / "metadata.parquet"
        # ParquetFile avoids treating the enclosing ``year=YYYY`` directory as
        # a Hive partition, which conflicts with the file's own string `year`.
        table = pq.ParquetFile(metadata_path).read(columns=METADATA_FIELDS)
        cache[metadata_year] = {
            str(row["path"]): row
            for row in table.to_pylist()
        }
    return cache[metadata_year]


def extract_ocr_page(page: pymupdf.Page, dpi: int) -> str:
    """OCR a rendered page. This runs only for quality-flagged source PDFs."""

    scale = dpi / 72
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csGRAY, alpha=False)
    result = subprocess.run(
        ["tesseract", "stdin", "stdout", "-l", "eng", "--psm", "6", "--dpi", str(dpi)],
        input=pixmap.tobytes("png"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def extract_pages(pdf_path: Path, use_ocr: bool, ocr_dpi: int) -> tuple[list[str], str, list[str]]:
    with pymupdf.open(pdf_path) as document:
        pages = (
            [extract_ocr_page(page, ocr_dpi) for page in document]
            if use_ocr
            else [page.get_text("text", sort=True) for page in document]
        )
    status, reasons = classify(text_metrics("\n".join(pages)))
    return pages, ("tesseract-eng" if use_ocr else "pymupdf-native"), reasons if status != "pass" else []


def process_year(
    corpus_root: Path,
    year: int,
    max_words: int,
    max_sentences: int,
    metadata_cache: dict[int, dict[str, dict[str, object]]],
    repair_source_ids: set[str] | None = None,
    ocr_dpi: int = 250,
) -> dict[str, int]:
    pdf_dir = corpus_root / "ecourts" / "pdfs" / f"year={year}"
    output_dir = corpus_root / "ecourts" / "cleaned" / f"year={year}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "chunks.jsonl"

    if not pdf_dir.exists():
        return {"year": year, "documents": 0, "chunks": 0, "missing_metadata": 0}

    documents = chunks = missing_metadata = excluded_non_evidentiary_chunks = residual_low_quality_documents = 0
    repair_outcomes: list[dict[str, object]] = []
    temporary_path = output_path.with_suffix(".jsonl.part")
    with temporary_path.open("w", encoding="utf-8") as output:
        if repair_source_ids is not None and output_path.exists():
            with output_path.open("r", encoding="utf-8") as existing:
                for line in existing:
                    if json.loads(line)["source_id"] not in repair_source_ids:
                        output.write(line)
        for pdf_path in sorted(pdf_dir.glob("*_EN.pdf")):
            source_path = pdf_path.stem.removesuffix("_EN")
            if repair_source_ids is not None and source_path not in repair_source_ids:
                continue
            metadata_year = int(source_path[:4]) if source_path[:4].isdigit() else year
            metadata = load_metadata(corpus_root, metadata_year, metadata_cache)
            if source_path not in metadata:
                missing_metadata += 1
                continue
            row = metadata[source_path]
            documents += 1
            raw_pages, extraction_method, residual_reasons = extract_pages(
                pdf_path, use_ocr=repair_source_ids is not None, ocr_dpi=ocr_dpi
            )
            if residual_reasons:
                residual_low_quality_documents += 1
                if repair_source_ids is not None:
                    repair_outcomes.append({
                        "source_id": source_path,
                        "status": "excluded_residual_low_quality",
                        "extraction_method": extraction_method,
                        "reasons": residual_reasons,
                    })
                continue
            if repair_source_ids is not None:
                repair_outcomes.append({
                    "source_id": source_path,
                    "status": "included",
                    "extraction_method": extraction_method,
                    "reasons": [],
                })
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
                        field: (None if row[field] is None else str(row[field]))
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
                        "cleaning_version": "v2-quality-gated-ocr" if repair_source_ids is not None else "v2-quality-gated-native",
                        "extraction_method": extraction_method,
                    })
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    chunks += 1
    temporary_path.replace(output_path)
    return {
        "year": year,
        "documents": documents,
        "chunks": chunks,
        "missing_metadata": missing_metadata,
        "excluded_non_evidentiary_chunks": excluded_non_evidentiary_chunks,
        "residual_low_quality_documents": residual_low_quality_documents,
        "repair_outcomes": repair_outcomes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2020)
    parser.add_argument("--max-words", type=int, default=220)
    parser.add_argument("--max-sentences", type=int, default=4)
    parser.add_argument("--repair-report", type=Path, help="Full quality-audit JSON; its failed source IDs are rebuilt with OCR.")
    parser.add_argument("--ocr-dpi", type=int, default=250)
    args = parser.parse_args()

    repair_source_ids: set[str] | None = None
    if args.repair_report:
        audit = json.loads(args.repair_report.read_text(encoding="utf-8"))
        repair_source_ids = {str(record["source_id"]) for record in audit["records"]}
    metadata_cache: dict[int, dict[str, dict[str, object]]] = {}
    results = [process_year(args.corpus_root, year, args.max_words, args.max_sentences, metadata_cache,
                            repair_source_ids, args.ocr_dpi)
               for year in range(args.start_year, args.end_year + 1)]
    record = {
        "updated_at_utc": datetime.now(UTC).isoformat(),
        "cleaning_version": "v2-quality-gated-ocr" if repair_source_ids is not None else "v2-quality-gated-native",
        "chunking": {"max_words": args.max_words, "max_sentences": args.max_sentences},
        "repair_source_ids": sorted(repair_source_ids) if repair_source_ids is not None else [],
        "ocr_dpi": args.ocr_dpi if repair_source_ids is not None else None,
        "years": results,
    }
    output = args.corpus_root / "ecourts" / "cleaning_record.json"
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
