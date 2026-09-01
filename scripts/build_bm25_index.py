"""Build a disk-backed SQLite FTS5 BM25 index from PostgreSQL provenance."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from load_provenance import DEFAULT_DATABASE_URL


INDEX_VERSION = "fts5-bm25-unicode61-temporal-v2"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--index", type=Path, default=Path("retrieval/bm25.sqlite"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/bm25_index.json"))
    parser.add_argument("--batch-size", type=int, default=10_000)
    args = parser.parse_args()

    if args.batch_size < 1:
        raise ValueError("batch size must be positive")
    args.index.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.index.with_suffix(args.index.suffix + ".part")
    if temporary.exists():
        temporary.unlink()

    sqlite = sqlite3.connect(temporary)
    try:
        sqlite.execute("PRAGMA journal_mode=OFF")
        sqlite.execute("PRAGMA synchronous=OFF")
        sqlite.execute("PRAGMA temp_store=MEMORY")
        sqlite.execute(
            "CREATE VIRTUAL TABLE chunks_fts USING fts5("
            "chunk_id UNINDEXED, chunk_text, tokenize='unicode61 remove_diacritics 2')"
        )
        # Keep only the exact date-derived year needed to apply the already
        # frozen temporal rule inside the candidate query.  This lets SQLite
        # restrict the candidate set *before* BM25's ORDER BY/LIMIT rather
        # than discarding future/same-year hits after a global top-k search.
        sqlite.execute(
            "CREATE TABLE chunk_temporal_metadata ("
            "chunk_id TEXT PRIMARY KEY, decision_year INTEGER NOT NULL)"
        )
        sqlite.execute(
            "CREATE INDEX chunk_temporal_metadata_year_idx "
            "ON chunk_temporal_metadata (decision_year)"
        )
        indexed = 0
        with psycopg.connect(args.database_url) as connection:
            with connection.cursor(name="corpus_chunks_for_bm25") as cursor:
                cursor.execute(
                    "SELECT chunk_id, chunk_text, EXTRACT(YEAR FROM decision_date)::INTEGER "
                    "FROM corpus_chunks ORDER BY chunk_id"
                )
                while batch := cursor.fetchmany(args.batch_size):
                    sqlite.executemany(
                        "INSERT INTO chunks_fts (chunk_id, chunk_text) VALUES (?, ?)",
                        [(row[0], row[1]) for row in batch],
                    )
                    sqlite.executemany(
                        "INSERT INTO chunk_temporal_metadata (chunk_id, decision_year) VALUES (?, ?)",
                        [(row[0], row[2]) for row in batch],
                    )
                    sqlite.commit()
                    indexed += len(batch)
        sqlite.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('optimize')")
        sqlite.commit()
    finally:
        sqlite.close()

    temporary.replace(args.index)
    result = {
        "built_at_utc": datetime.now(UTC).isoformat(),
        "index_version": INDEX_VERSION,
        "engine": "SQLite FTS5 bm25()",
        "tokenizer": "unicode61 remove_diacritics 2",
        "chunks_indexed": indexed,
        "index_path": str(args.index),
        "index_bytes": args.index.stat().st_size,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
