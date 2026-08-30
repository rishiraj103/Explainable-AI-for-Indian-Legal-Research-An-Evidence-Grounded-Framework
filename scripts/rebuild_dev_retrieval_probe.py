"""Build the corrected, alignment-gated development-only retrieval probe.

The probe is deliberately separate from the fixed-test authority answer key.
Each query source must already be an accepted row in ``dedup_matches.csv``;
numeric identifier equality is never consulted.  The authority is verified by
an explicit earlier-case citation in that aligned query source.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re

import pandas as pd
import psycopg
import pyarrow.parquet as pq

from legal_xai.alignment import (
    DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES,
    shared_six_token_phrases,
    title_party_alignment,
)
from legal_xai.answer_key import is_dev_only_case, load_split_ids, mirror_source_quality_status


DATABASE_URL = "postgresql://legal_xai:legal_xai_local_only_2026@127.0.0.1:54329/legal_xai"

# Each authority was identified from an explicit SCR citation in the aligned
# query judgment.  These are candidate *authority* IDs, not query ID matches.
PROBE_SPECS = (
    ("1980_104", "1979_2_699_716", "cited", None),
    ("1982_186", "1980_1_736_758", "cited", None),
    ("1984_62", "1964_3_164_190", "cited", None),
    ("1986_70", "1981_2_111_154", "cited", None),
    ("1988_238", "1982_3_411_443", "cited", None),
    # The query uses the ITR / AIR parallel forms, while corpus metadata uses SCR.
    ("1990_651", "1966_2_596_606", "referred_to", "[1966] 59 ITR 718"),
    ("1992_137", "1982_2_365_1455", "referred_to", None),
    ("1992_464", "S_1963_2_216_234", "referred_to", "AIR 1963 SC 906"),
    ("1993_66", "1976_2_347_676", "referred_to", None),
)


def source_url(source_id: str) -> str:
    year = source_id.removeprefix("S_")[:4]
    return (
        "https://indian-supreme-court-judgments.s3.amazonaws.com/"
        f"data/pdf/year={year}/english/{source_id}_EN.pdf"
    )


def citation_is_present(text: str, citation: str) -> bool:
    """Confirm that a reporter citation is present despite harmless OCR punctuation."""
    numbers = re.findall(r"\d+", citation)
    if len(numbers) < 2:
        return False
    if citation.casefold().startswith("air"):
        return re.search(
            rf"air\D{{0,12}}{numbers[0]}\D{{0,12}}s\D{{0,3}}c\D{{0,12}}{numbers[1]}",
            text,
            flags=re.IGNORECASE,
        ) is not None
    # A reporter is a required anchor so a coincidental year/page sequence does
    # not count.  The source can cite a documented parallel form (SCR/ITR/AIR).
    pattern = rf"{numbers[0]}\D{{0,24}}(?:supp\D{{0,12}})?{numbers[1]}\D{{0,16}}(?:s\D{{0,3}}c\D{{0,3}}r|i\D{{0,3}}t\D{{0,3}}r|air)"
    if len(numbers) >= 3:
        pattern += rf"\D{{0,24}}{numbers[2]}"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def fetch_source_texts(source_ids: set[str], database_url: str) -> dict[str, str]:
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT source_id, string_agg(chunk_text, ' ' ORDER BY page_number, passage_start_char) "
            "FROM corpus_chunks WHERE source_id = ANY(%s) GROUP BY source_id",
            (sorted(source_ids),),
        )
        return {str(source_id): str(text or "") for source_id, text in cursor.fetchall()}


def load_ildc_texts() -> tuple[dict[str, str], dict[str, str]]:
    texts: dict[str, str] = {}
    splits: dict[str, str] = {}
    for split in ("train", "validation"):
        table = pq.read_table(f"corpus/ildc/single_{split}.parquet", columns=["id", "text"])
        for row in table.to_pylist():
            case_id = str(row["id"])
            texts[case_id] = str(row["text"] or "")
            splits[case_id] = split
    return texts, splits


def load_metadata() -> pd.DataFrame:
    fields = ["title", "petitioner", "respondent", "citation", "decision_date", "path"]
    metadata = pd.concat(
        [pd.read_parquet(path, columns=fields) for path in Path("corpus/ecourts/metadata").glob("year=*/metadata.parquet")],
        ignore_index=True,
    ).drop_duplicates(subset=["path"])
    metadata = metadata.rename(columns={"path": "source_id"})
    metadata["source_id"] = metadata["source_id"].astype(str)
    return metadata.set_index("source_id", drop=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("answer_key/dev_retrieval_probe.json"))
    parser.add_argument("--database-url", default=DATABASE_URL)
    args = parser.parse_args()

    crosswalk = pd.read_csv("corpus/dedup_matches.csv")
    crosswalk["ildc_id"] = crosswalk["ildc_id"].astype(str)
    crosswalk["source_id"] = crosswalk["source_id"].astype(str)
    metadata = load_metadata()
    ildc_texts, source_splits = load_ildc_texts()
    train = load_split_ids("corpus/ildc/single_train.parquet")
    validation = load_split_ids("corpus/ildc/single_validation.parquet")
    test = load_split_ids("corpus/ildc/single_test.parquet")

    source_ids = {authority_id for _, authority_id, _, _ in PROBE_SPECS}
    query_source_by_case: dict[str, str] = {}
    for case_id, _, _, _ in PROBE_SPECS:
        rows = crosswalk.loc[crosswalk["ildc_id"] == case_id]
        if len(rows) != 1:
            raise ValueError(f"{case_id}: expected exactly one accepted crosswalk mapping, got {len(rows)}")
        query_source_by_case[case_id] = str(rows.iloc[0]["source_id"])
        source_ids.add(query_source_by_case[case_id])
    texts = fetch_source_texts(source_ids, args.database_url)

    entries: list[dict[str, object]] = []
    for case_id, authority_source_id, relationship, citation_used_in_query in PROBE_SPECS:
        if not is_dev_only_case(case_id, train, validation, test):
            raise ValueError(f"{case_id}: not strictly train/validation-only")
        query_source_id = query_source_by_case[case_id]
        if query_source_id not in metadata.index or authority_source_id not in metadata.index:
            raise ValueError(f"{case_id}: source metadata is unavailable")
        if not texts.get(query_source_id) or not texts.get(authority_source_id):
            raise ValueError(f"{case_id}: source text is unavailable")
        query_meta = metadata.loc[query_source_id]
        authority_meta = metadata.loc[authority_source_id]
        query_date = date.fromisoformat(pd.to_datetime(query_meta["decision_date"], dayfirst=True).date().isoformat())
        authority_date = date.fromisoformat(pd.to_datetime(authority_meta["decision_date"], dayfirst=True).date().isoformat())
        if authority_date >= query_date:
            raise ValueError(f"{case_id}: authority is not earlier than query")
        verified_citation = citation_used_in_query or str(authority_meta["citation"])
        if not citation_is_present(texts[query_source_id], verified_citation):
            raise ValueError(f"{case_id}: authority citation not found in aligned query source")
        title_passed, shared_terms, coverage = title_party_alignment(
            ildc_texts[case_id], query_meta["title"], query_meta["petitioner"], query_meta["respondent"],
        )
        phrase_count, example_phrase = shared_six_token_phrases(
            ildc_texts[case_id], texts[query_source_id],
        )
        if not title_passed or phrase_count < DEFAULT_MIN_DIRECT_SIX_TOKEN_PHRASES:
            raise ValueError(f"{case_id}: accepted crosswalk failed re-validation")
        query_quality = mirror_source_quality_status(query_source_id)
        authority_quality = mirror_source_quality_status(authority_source_id)
        if "excluded_low_quality" in {query_quality, authority_quality}:
            raise ValueError(f"{case_id}: cannot use permanently excluded source")
        entries.append({
            "split": "dev",
            "source_split": source_splits[case_id],
            "query_case_id": case_id,
            "query_case_title": str(query_meta["title"]),
            "query_decision_date": query_date.isoformat(),
            "query_source_id": query_source_id,
            "query_source_type": "eCourts-mirror",
            "query_source_url": source_url(query_source_id),
            "query_alignment_candidate_origin": str(crosswalk.loc[crosswalk["ildc_id"] == case_id].iloc[0]["candidate_origin"]),
            "query_alignment_title_party_passed": title_passed,
            "query_alignment_shared_identity_terms": list(shared_terms),
            "query_alignment_identity_coverage": round(coverage, 3),
            "query_alignment_direct_six_token_phrases": phrase_count,
            "query_alignment_example_phrase": example_phrase,
            "query_verification_method": query_quality,
            "authority_title": str(authority_meta["title"]),
            "authority_citation": verified_citation,
            "authority_corpus_citation": str(authority_meta["citation"]),
            "authority_decision_date": authority_date.isoformat(),
            "authority_source_id": authority_source_id,
            "authority_source_type": "eCourts-mirror",
            "authority_source_url": source_url(authority_source_id),
            "authority_passage_locator": f"Aligned query source explicitly cites {verified_citation}.",
            "authority_verification_method": authority_quality,
            "authority_citation_present_in_query_source": True,
            "relationship": relationship,
            "temporal_status": "eligible_by_year",
            "independent_of_system_retrieval": True,
            "verified_on": "2026-08-30",
        })

    if not 8 <= len(entries) <= 10:
        raise ValueError("probe must contain 8-10 entries")
    era_counts = Counter(int(entry["query_decision_date"][:4]) // 10 * 10 for entry in entries)
    payload = {
        "schema_version": "dev-retrieval-probe-v2",
        "purpose": (
            "Pre-freeze retrieval diagnosis only. Built after the identifier-namespace correction "
            "from alignment-gated train/validation mappings; never merge with evaluation metrics."
        ),
        "supersedes": "dev-retrieval-probe-v1 (invalidated because its query-source mappings predated the content-alignment gate)",
        "entries": entries,
        "era_distribution": {f"{era}s": era_counts[era] for era in sorted(era_counts)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} corrected dev-only retrieval probes to {args.output}")


if __name__ == "__main__":
    main()
