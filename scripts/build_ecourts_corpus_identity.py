"""Record a deterministic identity for the local cleaned eCourts corpus.

The raw PDFs and cleaned JSONL files are intentionally local-only.  This
script makes their final cleaned-corpus state independently verifiable without
committing the multi-gigabyte corpus: it hashes every cleaned JSONL file and
then hashes the sorted, length-delimited file manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256_and_line_count(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    line_count = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            line_count += block.count(b"\n")
    return digest.hexdigest(), line_count


def sha256(path: Path) -> str:
    return sha256_and_line_count(path)[0]


def update_length_delimited(digest: "hashlib._Hash", value: str) -> None:
    encoded = value.encode("utf-8")
    digest.update(len(encoded).to_bytes(8, "big"))
    digest.update(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cleaned-root", type=Path, default=ROOT / "corpus/ecourts/cleaned")
    parser.add_argument("--cleaning-record", type=Path, default=ROOT / "corpus/ecourts/cleaning_record.json")
    parser.add_argument("--bm25-index", type=Path, default=ROOT / "retrieval/bm25.sqlite")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/ecourts_corpus_identity.json")
    args = parser.parse_args()

    files = sorted(args.cleaned_root.rglob("chunks.jsonl"))
    if not files:
        raise FileNotFoundError(f"No cleaned chunk files found under {args.cleaned_root}")

    aggregate = hashlib.sha256()
    entries: list[dict[str, object]] = []
    total_bytes = 0
    chunk_count = 0
    for path in files:
        relative_path = path.relative_to(args.cleaned_root).as_posix()
        size = path.stat().st_size
        content_hash, file_chunk_count = sha256_and_line_count(path)
        entries.append({
            "path": relative_path,
            "bytes": size,
            "sha256": content_hash,
            "jsonl_record_count": file_chunk_count,
        })
        total_bytes += size
        chunk_count += file_chunk_count
        for value in (relative_path, str(size), content_hash):
            update_length_delimited(aggregate, value)

    # The current cleaning record is a hash-linked repair record; count final
    # chunks from the actual JSONL lines rather than its repair-only subtotal.
    result = {
        "identity_version": "ecourts-cleaned-corpus-identity-v1",
        "cleaned_corpus": {
            "root": "corpus/ecourts/cleaned",
            "included_files": "**/chunks.jsonl",
            "file_count": len(entries),
            "total_bytes": total_bytes,
            "jsonl_record_count": chunk_count,
            "aggregate_sha256_algorithm": "SHA-256 over sorted, length-delimited relative path, byte size, and per-file SHA-256 values",
            "aggregate_sha256": aggregate.hexdigest(),
            "files": entries,
        },
        "linked_final_artifacts": {
            "cleaning_record": {
                "path": "corpus/ecourts/cleaning_record.json",
                "sha256": sha256(args.cleaning_record),
            },
            "bm25_index": {
                "path": "retrieval/bm25.sqlite",
                "sha256": sha256(args.bm25_index),
                "bytes": args.bm25_index.stat().st_size,
            },
        },
        "guarantees": "This identifies the exact bytes of the final local cleaned JSONL corpus and links that corpus to the local cleaning record and BM25 index at generation time.",
        "does_not_guarantee": "It is not an immutable upstream S3 snapshot identifier, does not hash the raw PDFs, and does not substitute for a PostgreSQL volume dump. Reconstructing the database still requires loading this identified cleaned corpus with the tracked provenance loader.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "aggregate_sha256": aggregate.hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
