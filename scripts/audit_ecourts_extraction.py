"""Audit eCourts PDF text extraction quality before corpus rebuilds.

The eCourts files are English-language judgment PDFs.  This audit therefore
uses conservative, explainable signals for unreadable embedded text: missing
text, Unicode control/replacement characters, mojibake markers, and an
unexpectedly low proportion of ASCII legal-language tokens.  It does not alter
source PDFs or cleaned chunks.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import unicodedata
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pymupdf


MOJIBAKE_MARKERS = re.compile(r"[\u0080-\u009f\ufffd]|(?:Ã|Â|â)[^\s]")
ASCII_WORD = re.compile(r"[A-Za-z]{2,}")
TOKEN = re.compile(r"\S+")


def text_metrics(text: str) -> dict[str, float | int]:
    """Return deterministic quality signals for one extracted document."""

    nonspace = [char for char in text if not char.isspace()]
    total = len(nonspace)
    ascii_visible = sum(char.isascii() and char.isprintable() for char in nonspace)
    # Format characters (notably soft hyphens in older reports) are common in
    # otherwise readable PDFs.  Only count actual control/surrogate codepoints.
    controls = sum(
        unicodedata.category(char) in {"Cc", "Cs"} and char not in "\n\r\t" for char in text
    )
    replacements = text.count("\ufffd")
    tokens = TOKEN.findall(text)
    ascii_words = ASCII_WORD.findall(text)
    return {
        "nonspace_characters": total,
        "ascii_visible_ratio": round(ascii_visible / total, 6) if total else 0.0,
        "control_characters": controls,
        "replacement_characters": replacements,
        "mojibake_markers": len(MOJIBAKE_MARKERS.findall(text)),
        "tokens": len(tokens),
        "ascii_words": len(ascii_words),
        "ascii_words_per_token": round(len(ascii_words) / len(tokens), 6) if tokens else 0.0,
    }


def classify(metrics: dict[str, float | int]) -> tuple[str, list[str]]:
    """Classify the text quality using fixed pre-result thresholds."""

    reasons: list[str] = []
    if metrics["nonspace_characters"] < 80:
        reasons.append("insufficient_embedded_text")
    if metrics["control_characters"] > 0:
        reasons.append("unicode_control_characters")
    if metrics["replacement_characters"] >= 2:
        reasons.append("replacement_characters")
    if metrics["mojibake_markers"] >= 2:
        reasons.append("mojibake_markers")
    if metrics["nonspace_characters"] >= 80 and metrics["ascii_visible_ratio"] < 0.75:
        reasons.append("low_ascii_visible_ratio")
    if metrics["tokens"] >= 20 and metrics["ascii_words_per_token"] < 0.25:
        reasons.append("low_english_token_ratio")
    return ("needs_repair" if reasons else "pass", reasons)


def pdf_record(pdf_path: Path, corpus_root: Path) -> dict[str, object]:
    """Inspect native PDF text and page image presence without modifying it."""

    with pymupdf.open(pdf_path) as document:
        pages = [page.get_text("text", sort=True) for page in document]
        image_pages = sum(bool(page.get_images(full=True)) for page in document)
    text = "\n".join(pages)
    metrics = text_metrics(text)
    status, reasons = classify(metrics)
    return {
        "source_id": pdf_path.stem.removesuffix("_EN"),
        "pdf": str(pdf_path.relative_to(corpus_root)),
        "year": int(pdf_path.parent.name.removeprefix("year=")),
        "pages": len(pages),
        "pages_with_embedded_images": image_pages,
        "classification": status,
        "reasons": reasons,
        "metrics": metrics,
        "native_text_preview": text[:300].replace("\n", " "),
    }


def _audit_worker(values: tuple[Path, Path]) -> dict[str, object]:
    return pdf_record(*values)


def stratified_sample(pdf_root: Path, per_year: int, seed: int) -> list[Path]:
    rng = random.Random(seed)
    selected: list[Path] = []
    for year_dir in sorted(pdf_root.glob("year=*")):
        pdfs = sorted(year_dir.glob("*_EN.pdf"))
        if len(pdfs) <= per_year:
            selected.extend(pdfs)
        else:
            selected.extend(rng.sample(pdfs, per_year))
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    parser.add_argument("--per-year", type=int, default=2)
    parser.add_argument("--all", action="store_true", help="Audit every locally available PDF, not a sample.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--include", action="append", default=[], help="Source ID to include in addition to the sample.")
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/extraction_quality_scope.json"))
    parser.add_argument("--output-md", type=Path, default=Path("artifacts/extraction_quality_scope.md"))
    args = parser.parse_args()

    pdf_root = args.corpus_root / "ecourts" / "pdfs"
    if args.workers < 1:
        raise ValueError("--workers must be positive")
    selected = (
        sorted(pdf_root.glob("year=*/*_EN.pdf"))
        if args.all
        else stratified_sample(pdf_root, args.per_year, args.seed)
    )
    by_source = {path.stem.removesuffix("_EN"): path for path in pdf_root.glob("year=*/*_EN.pdf")}
    for source_id in args.include:
        if source_id not in by_source:
            raise FileNotFoundError(f"No raw PDF found for {source_id}")
        if by_source[source_id] not in selected:
            selected.append(by_source[source_id])

    work = [(path, args.corpus_root) for path in selected]
    if args.workers == 1:
        records = [_audit_worker(item) for item in work]
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            records = list(pool.map(_audit_worker, work, chunksize=16))
    counts = Counter(record["classification"] for record in records)
    reason_counts = Counter(reason for record in records for reason in record["reasons"])
    summary = {
        "audited_at_utc": datetime.now(UTC).isoformat(),
        "method": {
            "sampling": (
                "all locally available raw PDFs" if args.all
                else f"{args.per_year} seeded random raw PDFs per available year, plus named diagnostic PDFs"
            ),
            "seed": args.seed,
            "quality_bar": "pass only when native text has at least 80 non-whitespace characters, no Unicode control/surrogate codepoints, fewer than two replacement or mojibake markers, ASCII-visible ratio >=0.75, and English ASCII-word/token ratio >=0.25 where applicable",
            "scope": "Raw PDF embedded text, before cleaning/chunking; no source or derived data changed.",
        },
        "sample_size": len(records),
        "available_years": len(list(pdf_root.glob("year=*"))),
        "classification_counts": dict(counts),
        "reason_counts": dict(reason_counts),
        # A full audit retains only the actionable failure records, so its
        # artifact remains inspectable without becoming a second corpus copy.
        "records": records if not args.all else [record for record in records if record["classification"] == "needs_repair"],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# eCourts extraction-quality scope audit",
        "",
        (
            f"Audited all {len(records)} locally available raw PDFs across {summary['available_years']} years."
            if args.all
            else f"Audited {len(records)} raw PDFs across {summary['available_years']} available years using a seeded stratified sample plus named diagnostic PDFs."
        ),
        "",
        "## Result",
        "",
        f"- Pass: {counts['pass']}",
        f"- Needs repair: {counts['needs_repair']}",
        f"- Reasons: {', '.join(f'{name}={count}' for name, count in sorted(reason_counts.items())) or 'none'}",
        "",
        "The fixed quality bar is recorded in the JSON companion file. A `needs_repair` result means the current native-text extraction must not enter the rebuilt retrieval corpus without an approved fallback or explicit exclusion.",
        "",
        "## Flagged documents",
        "",
        "| Source ID | Year | Pages | Image pages | Reasons |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for record in summary["records"]:
        if record["classification"] == "needs_repair":
            lines.append(
                f"| {record['source_id']} | {record['year']} | {record['pages']} | {record['pages_with_embedded_images']} | {', '.join(record['reasons'])} |"
            )
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("sample_size", "classification_counts", "reason_counts")}, indent=2))


if __name__ == "__main__":
    main()
