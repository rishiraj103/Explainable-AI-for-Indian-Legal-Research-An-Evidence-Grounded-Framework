"""Read-only content-alignment audit for evaluation answer-key query sources.

Canonical case IDs are not treated as proof that an ILDC record and an
eCourts source are the same judgment.  This audit resolves the source recorded
for each evaluation entry and checks actual text alignment before any retrieval
metric may rely on that query-source mapping.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlparse

import psycopg
import pyarrow.parquet as pq


DATABASE_URL = "postgresql://legal_xai:legal_xai_local_only_2026@127.0.0.1:54329/legal_xai"
STOPWORDS = frozenset({
    "and", "anr", "another", "appeal", "appeals", "court", "etc", "for", "from", "has", "have", "in",
    "judgment", "law", "of", "or", "ors", "others", "the", "this", "to", "v", "versus", "with",
})
MIN_DIRECT_PHRASE_MATCHES = 100


def normalise_title(value: str | None) -> str:
    value = (value or "").casefold().replace("versus", " v ")
    value = re.sub(r"\bu\.?\s*p\.?\b", "uttar pradesh", value)
    return " ".join(
        token for token in re.findall(r"[a-z0-9]+", value)
        if token not in {"and", "anr", "another", "ors", "others", "etc", "of", "the"}
    )


def tokens(value: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", value.casefold())


def opening_excerpt(value: str, word_limit: int = 100) -> str:
    return " ".join(value.split()[:word_limit])


def source_id_from_url(url: str) -> str | None:
    filename = Path(urlparse(url).path).name
    match = re.fullmatch(r"(.+)_EN\.pdf", filename, flags=re.IGNORECASE)
    return match.group(1) if match else None


def phrase_match(ildc_tokens: list[str], source_tokens: list[str], width: int = 6) -> tuple[int, str | None]:
    if len(ildc_tokens) < width or len(source_tokens) < width:
        return 0, None
    ildc_shingles = {" ".join(ildc_tokens[index:index + width]) for index in range(len(ildc_tokens) - width + 1)}
    matches = 0
    first = None
    for index in range(len(source_tokens) - width + 1):
        shingle = " ".join(source_tokens[index:index + width])
        if shingle in ildc_shingles:
            matches += 1
            first = first or shingle
    return matches, first


def subject_terms(ildc_tokens: list[str], source_tokens: list[str]) -> list[str]:
    shared = (Counter(ildc_tokens) & Counter(source_tokens))
    return [
        token for token, _ in shared.most_common()
        if token not in STOPWORDS and len(token) >= 5
    ][:12]


def load_ildc_texts(case_ids: set[str]) -> dict[str, str]:
    table = pq.read_table("corpus/ildc/single_test.parquet", columns=["id", "text"])
    return {
        str(row["id"]): str(row["text"] or "")
        for row in table.to_pylist() if str(row["id"]) in case_ids
    }


def load_source_metadata() -> dict[str, tuple[str, str]]:
    """Return source ID -> title and ISO date without loading every corpus text."""
    with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT source_id, max(title), max(decision_date)::text "
            "FROM corpus_chunks GROUP BY source_id"
        )
        return {str(row[0]): (str(row[1] or ""), str(row[2])) for row in cursor.fetchall()}


def load_source_texts(source_ids: set[str]) -> dict[str, str]:
    with psycopg.connect(DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT source_id, string_agg(chunk_text, ' ' ORDER BY page_number, passage_start_char) "
            "FROM corpus_chunks WHERE source_id = ANY(%s) GROUP BY source_id",
            (sorted(source_ids),),
        )
        return {str(row[0]): str(row[1] or "") for row in cursor.fetchall()}


def resolve_source(entry: dict[str, object], sources: dict[str, tuple[str, str]]) -> tuple[str | None, str]:
    direct = source_id_from_url(str(entry.get("query_source_url", "")))
    if direct in sources:
        return direct, "source_id_from_eCourts_URL"
    expected_title = normalise_title(str(entry.get("query_case_title", "")))
    expected_date = str(entry.get("query_decision_date", ""))
    matches = [source_id for source_id, (title, decision_date) in sources.items()
               if normalise_title(title) == expected_title and decision_date == expected_date]
    if len(matches) == 1:
        return matches[0], "title_and_exact_date"
    return None, "unresolved_source"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answer-key", type=Path, default=Path("answer_key/authority_answer_key.json"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    entries = [entry for entry in json.loads(args.answer_key.read_text(encoding="utf-8"))["entries"]
               if entry.get("status") == "evaluation"]
    case_ids = {str(entry["query_case_id"]) for entry in entries}
    ildc_texts = load_ildc_texts(case_ids)
    if ildc_texts.keys() != case_ids:
        raise ValueError(f"fixed-test records missing: {sorted(case_ids - ildc_texts.keys())}")
    sources = load_source_metadata()
    resolved = {str(entry["query_case_id"]): resolve_source(entry, sources) for entry in entries}
    source_texts = load_source_texts({source_id for source_id, _ in resolved.values() if source_id})
    rows: list[dict[str, object]] = []
    for entry in entries:
        case_id = str(entry["query_case_id"])
        source_id, resolution = resolved[case_id]
        if source_id is None:
            rows.append({"query_case_id": case_id, "status": "fail_unresolved_source", "source_resolution": resolution})
            continue
        source_title, source_date = sources[source_id]
        source_text = source_texts[source_id]
        ildc_tokens = tokens(ildc_texts[case_id])
        source_tokens = tokens(source_text)
        phrase_matches, first_phrase = phrase_match(ildc_tokens, source_tokens)
        party_tokens = [token for token in tokens(source_title) if token not in STOPWORDS and len(token) >= 4]
        party_overlap = sorted(set(party_tokens) & set(ildc_tokens))
        shared_subject_terms = subject_terms(ildc_tokens, source_tokens)
        status = "pass" if phrase_matches >= MIN_DIRECT_PHRASE_MATCHES else "fail_content_mismatch"
        rows.append({
            "query_case_id": case_id,
            "answer_key_title": entry["query_case_title"],
            "source_id": source_id,
            "source_title": source_title,
            "source_decision_date": source_date,
            "source_resolution": resolution,
            "status": status,
            "party_name_overlap_terms": party_overlap,
            "party_name_signal": bool(party_overlap),
            "shared_subject_or_posture_terms": shared_subject_terms,
            "subject_posture_signal": len(shared_subject_terms) >= 3,
            "direct_six_token_phrase_matches": phrase_matches,
            "example_shared_six_token_phrase": first_phrase,
            "ildc_opening_excerpt": opening_excerpt(ildc_texts[case_id]),
            "source_opening_excerpt": opening_excerpt(source_text),
        })
    counts = Counter(str(row["status"]) for row in rows)
    payload = {
        "audit_version": "answer-key-content-alignment-v1",
        "audit_date": date.today().isoformat(),
        "scope": "read-only audit of all evaluation entries; no retrieval settings or answer-key entries were changed",
        "method": {
            "decisive_signal": "at least 100 direct shared six-token text phrases between ILDC judgment text and the resolved eCourts source document",
            "supplementary_signals": ["party-name token overlap", "shared subject/procedural vocabulary"],
            "source_resolution": "direct eCourts URL when available, otherwise normalized title plus exact decision date",
        },
        "summary": {"total": len(rows), **counts},
        "rows": rows,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = [
        "# Evaluation answer-key content-alignment audit",
        "",
        "Read-only audit of all 30 evaluation entries after the dev-probe misalignment catch. A pass requires at least 100 direct shared six-token phrases between the fixed-test ILDC text and its resolved eCourts query-source document. This conservative threshold follows the observed separation: aligned documents have 372–9,199 shared phrases, while apparent mismatches have 0–10. Party-name and subject/procedural term signals are supplementary; side-by-side opening excerpts are recorded in JSON for every row.",
        "",
        f"**Result:** {len(rows)} total; " + ", ".join(f"{key}: {value}" for key, value in sorted(counts.items())),
        "",
        "| ILDC case | Resolved eCourts source | Resolution | Direct phrases | Party signal | Subject/posture signal | Status |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        markdown.append(
            f"| `{row['query_case_id']}` | `{row.get('source_id', '—')}` | {row['source_resolution']} | "
            f"{row.get('direct_six_token_phrase_matches', '—')} | {row.get('party_name_signal', '—')} | "
            f"{row.get('subject_posture_signal', '—')} | {row['status']} |"
        )
    args.markdown_output.write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(f"Audited {len(rows)} evaluation entries: {dict(counts)}")


if __name__ == "__main__":
    main()
