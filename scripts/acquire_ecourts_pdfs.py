"""Acquire English eCourts judgment PDFs by year from the public S3 archive.

The download is deliberately sequential and resumable. It downloads only the
English PDF archives declared by the source's per-year index, extracts their
PDFs into the local corpus, and deletes successful temporary archives. It does
not extract text, create chunks, or build an index.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tarfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path


S3_BASE = "https://indian-supreme-court-judgments.s3.amazonaws.com"


def fetch_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def download_file(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    temporary.replace(destination)


def extract_english_pdfs(archive: Path, destination: Path) -> int:
    """Extract only safe English PDF members, preserving existing files."""

    destination.mkdir(parents=True, exist_ok=True)
    extracted = 0
    with tarfile.open(archive, "r") as tar:
        for member in tar:
            member_path = Path(member.name)
            if not member.isfile() or member_path.suffix.lower() != ".pdf" or not member_path.name.endswith("_EN.pdf"):
                continue
            target = destination / member_path.name
            if target.exists() and target.stat().st_size == member.size:
                continue
            source = tar.extractfile(member)
            if source is None:
                continue
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            extracted += 1
    return extracted


def acquire_year(corpus_root: Path, year: int) -> dict[str, object]:
    index_url = f"{S3_BASE}/data/tar/year={year}/english/english.index.json"
    index = fetch_json(index_url)
    pdf_dir = corpus_root / "ecourts" / "pdfs" / f"year={year}"
    archive_dir = corpus_root / "ecourts" / "archives" / f"year={year}"
    extracted = 0
    for part in index["parts"]:
        archive_name = part["name"]
        archive = archive_dir / archive_name
        download_file(f"{S3_BASE}/data/tar/year={year}/english/{archive_name}", archive)
        extracted += extract_english_pdfs(archive, pdf_dir)
        archive.unlink()
    return {
        "year": year,
        "source_file_count": index["file_count"],
        "source_archive_bytes": index["total_size"],
        "new_pdfs_extracted": extracted,
        "local_pdf_count": len(list(pdf_dir.glob("*_EN.pdf"))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2020)
    args = parser.parse_args()

    results = [acquire_year(args.corpus_root, year) for year in range(args.start_year, args.end_year + 1)]
    record = {
        "updated_at_utc": datetime.now(UTC).isoformat(),
        "scope": {"start_year": args.start_year, "end_year": args.end_year, "language": "English"},
        "years": results,
    }
    (args.corpus_root / "ecourts" / "acquisition_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
