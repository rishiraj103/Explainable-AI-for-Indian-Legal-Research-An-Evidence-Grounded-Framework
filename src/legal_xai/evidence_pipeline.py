"""Reusable temporal-safe candidate retrieval for the evidence pipeline.

This module deliberately stops at provenance-linked candidate retrieval.  It
does not generate legal answers; grounded answer generation belongs to Week 8.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import psycopg

from legal_xai.retrieval import exclude_query_duplicate, fts_query, query_exclusion_cases
from legal_xai.temporal import assess_temporal_eligibility


TEMPORAL_POLICY = "precedent_decision_year < ildc_query_year; same-year excluded as ambiguous"


@dataclass(frozen=True)
class EvidenceCandidate:
    rank: int
    chunk_id: str
    source_id: str
    case_id: str | None
    citation: str | None
    decision_date: str
    court: str
    pdf_file: str
    page_number: int
    passage_start_char: int
    passage_end_char: int
    bm25_score: float
    temporal_status: str
    text: str

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class CandidateRetrieval:
    run_id: str
    query_id: str
    query_year: int
    query: str
    candidates: tuple[EvidenceCandidate, ...]
    query_duplicate_chunks_excluded: int

    @property
    def status_counts(self) -> dict[str, int]:
        return {
            status: sum(candidate.temporal_status == status for candidate in self.candidates)
            for status in ("eligible", "ambiguous_excluded", "ineligible", "excluded_missing_metadata")
        }


def retrieve_temporal_candidates(
    *,
    query_id: str,
    query_year: int,
    query: str,
    candidate_k: int,
    index_path: Path,
    database_url: str,
    dedup_matches: Path,
    index_version: str,
) -> CandidateRetrieval:
    """Retrieve and log a provenance-linked candidate set for one legal query."""

    if candidate_k < 1:
        raise ValueError("candidate_k must be positive")
    audited_near_cases = query_exclusion_cases(query_id, dedup_matches)
    with sqlite3.connect(index_path) as index:
        rows = index.execute(
            "SELECT chunk_id, bm25(chunks_fts) AS raw_score "
            "FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY raw_score LIMIT ?",
            (fts_query(query), candidate_k),
        ).fetchall()
    if not rows:
        raise ValueError("BM25 returned no candidates for the supplied query")

    chunk_ids = [row[0] for row in rows]
    run_id = uuid.uuid4()
    candidates: list[EvidenceCandidate] = []
    duplicate_excluded = 0
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT chunk_id, source_id, case_id, citation, decision_date, court, pdf_file, page_number, "
                "passage_start_char, passage_end_char, chunk_text "
                "FROM corpus_chunks WHERE chunk_id = ANY(%s)",
                (chunk_ids,),
            )
            metadata = {row[0]: row for row in cursor.fetchall()}
            for rank, (chunk_id, raw_score) in enumerate(rows, start=1):
                row = metadata[chunk_id]
                if exclude_query_duplicate(query_id, row[2], audited_near_cases):
                    duplicate_excluded += 1
                    continue
                temporal = assess_temporal_eligibility(query_year, row[4])
                candidates.append(EvidenceCandidate(
                    rank=rank,
                    chunk_id=row[0], source_id=row[1], case_id=row[2], citation=row[3],
                    decision_date=row[4].isoformat(), court=row[5], pdf_file=row[6],
                    page_number=row[7], passage_start_char=row[8], passage_end_char=row[9],
                    bm25_score=-float(raw_score), temporal_status=temporal.status.value, text=row[10],
                ))
            cursor.execute(
                "INSERT INTO retrieval_runs (run_id, query_id, query_year, query_text, index_version, "
                "created_at_utc, temporal_policy) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (run_id, query_id, query_year, query, index_version, datetime.now(UTC), TEMPORAL_POLICY),
            )
            cursor.executemany(
                "INSERT INTO retrieval_results (run_id, rank, chunk_id, bm25_score, temporal_status) "
                "VALUES (%s, %s, %s, %s, %s)",
                [(run_id, item.rank, item.chunk_id, item.bm25_score, item.temporal_status) for item in candidates],
            )
        connection.commit()
    return CandidateRetrieval(
        run_id=str(run_id), query_id=query_id, query_year=query_year, query=query,
        candidates=tuple(candidates), query_duplicate_chunks_excluded=duplicate_excluded,
    )
