"""Load cleaned eCourts chunk provenance into local PostgreSQL.

The loader is intentionally separate from retrieval indexing. It records every
chunk's stable source ID, source locator, decision date, and text so BM25
retrieval runs can later be traced through ``retrieval_runs`` and
``retrieval_results``.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, date, datetime
from pathlib import Path

import psycopg


DEFAULT_DATABASE_URL = "postgresql://legal_xai:legal_xai_local_only_2026@127.0.0.1:54329/legal_xai"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS corpus_chunks (
    chunk_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    case_id TEXT,
    citation TEXT,
    decision_date DATE NOT NULL,
    court TEXT NOT NULL,
    title TEXT,
    petitioner TEXT,
    respondent TEXT,
    disposal_nature TEXT,
    source_path TEXT NOT NULL,
    pdf_file TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    passage_start_char INTEGER NOT NULL,
    passage_end_char INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    cleaning_version TEXT NOT NULL,
    UNIQUE (source_id, page_number, passage_start_char, passage_end_char)
);

CREATE TABLE IF NOT EXISTS retrieval_runs (
    run_id UUID PRIMARY KEY,
    query_id TEXT NOT NULL,
    query_year INTEGER NOT NULL,
    query_text TEXT NOT NULL,
    index_version TEXT NOT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL,
    temporal_policy TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retrieval_results (
    run_id UUID NOT NULL REFERENCES retrieval_runs(run_id) ON DELETE CASCADE,
    rank INTEGER NOT NULL CHECK (rank > 0),
    chunk_id TEXT NOT NULL REFERENCES corpus_chunks(chunk_id),
    bm25_score DOUBLE PRECISION NOT NULL,
    temporal_status TEXT NOT NULL,
    PRIMARY KEY (run_id, rank),
    UNIQUE (run_id, chunk_id)
);
"""


def parse_ecourts_date(value: str) -> date:
    return datetime.strptime(value, "%d-%m-%Y").date()


def chunk_rows(corpus_root: Path, start_year: int, end_year: int):
    for year in range(start_year, end_year + 1):
        source = corpus_root / "ecourts" / "cleaned" / f"year={year}" / "chunks.jsonl"
        with source.open("r", encoding="utf-8") as lines:
            for line in lines:
                record = json.loads(line)
                yield (
                    record["chunk_id"], record["source_id"], record.get("case_id"), record.get("citation"),
                    parse_ecourts_date(record["decision_date"]), record["court"], record.get("title"),
                    record.get("petitioner"), record.get("respondent"), record.get("disposal_nature"),
                    record["path"], record["pdf_file"], record["page_number"], record["passage_start_char"],
                    record["passage_end_char"], record["text"], record["cleaning_version"],
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2020)
    parser.add_argument("--database-url", default=os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--output", type=Path, default=Path("artifacts/provenance_load.json"))
    args = parser.parse_args()

    with psycopg.connect(args.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)
            cursor.execute("TRUNCATE retrieval_results, retrieval_runs, corpus_chunks")
            copy_sql = """
                COPY corpus_chunks (
                    chunk_id, source_id, case_id, citation, decision_date, court, title, petitioner, respondent,
                    disposal_nature, source_path, pdf_file, page_number, passage_start_char, passage_end_char,
                    chunk_text, cleaning_version
                ) FROM STDIN
            """
            source_rows_read = 0
            chunks_loaded = 0
            duplicate_chunk_ids_skipped = 0
            seen_chunk_ids: set[str] = set()
            with cursor.copy(copy_sql) as copy:
                for row in chunk_rows(args.corpus_root, args.start_year, args.end_year):
                    source_rows_read += 1
                    if row[0] in seen_chunk_ids:
                        duplicate_chunk_ids_skipped += 1
                        continue
                    seen_chunk_ids.add(row[0])
                    copy.write_row(row)
                    chunks_loaded += 1
            cursor.execute("CREATE INDEX IF NOT EXISTS corpus_chunks_decision_date_idx ON corpus_chunks (decision_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS corpus_chunks_source_id_idx ON corpus_chunks (source_id)")
        connection.commit()

    result = {
        "loaded_at_utc": datetime.now(UTC).isoformat(),
        "database": "local Docker PostgreSQL",
        "years": [args.start_year, args.end_year],
        "source_rows_read": source_rows_read,
        "unique_chunks_loaded": chunks_loaded,
        "duplicate_chunk_ids_skipped": duplicate_chunk_ids_skipped,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
