"""Validate that the retrieval probe is dev-only and source-verification ready."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

from legal_xai.answer_key import is_dev_only_case, load_split_ids, mirror_source_quality_status


REQUIRED_FIELDS = {
    "split", "source_split", "query_case_id", "query_source_id", "query_decision_date",
    "authority_source_id", "authority_decision_date", "authority_source_type",
    "authority_passage_locator", "authority_verification_method", "independent_of_system_retrieval",
    "query_alignment_title_party_passed", "query_alignment_direct_six_token_phrases",
    "authority_citation_present_in_query_source",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, default=Path("answer_key/dev_retrieval_probe.json"))
    args = parser.parse_args()
    payload = json.loads(args.probe.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "dev-retrieval-probe-v2":
        raise SystemExit("REJECTED: unexpected dev-probe schema version")
    train = load_split_ids("corpus/ildc/single_train.parquet")
    validation = load_split_ids("corpus/ildc/single_validation.parquet")
    test = load_split_ids("corpus/ildc/single_test.parquet")
    ids: set[str] = set()
    for entry in payload.get("entries", []):
        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            raise SystemExit(f"REJECTED: {entry.get('query_case_id')} lacks {sorted(missing)}")
        query_id = str(entry["query_case_id"])
        if entry["split"] != "dev" or not is_dev_only_case(query_id, train, validation, test):
            raise SystemExit(f"REJECTED: {query_id} is not dev-only")
        if query_id in ids:
            raise SystemExit(f"REJECTED: duplicate query ID {query_id}")
        ids.add(query_id)
        if entry["source_split"] not in {"train", "validation"}:
            raise SystemExit(f"REJECTED: {query_id} has invalid source split")
        if not entry["query_alignment_title_party_passed"]:
            raise SystemExit(f"REJECTED: {query_id} failed title/party alignment")
        if int(entry["query_alignment_direct_six_token_phrases"]) < 100:
            raise SystemExit(f"REJECTED: {query_id} failed direct content alignment")
        if not entry["authority_citation_present_in_query_source"]:
            raise SystemExit(f"REJECTED: {query_id} authority citation was not source-verified")
        if date.fromisoformat(entry["authority_decision_date"]) >= date.fromisoformat(entry["query_decision_date"]):
            raise SystemExit(f"REJECTED: {query_id} has a temporally ineligible authority")
        for source_id in (entry["query_source_id"], entry["authority_source_id"]):
            if mirror_source_quality_status(source_id) == "excluded_low_quality":
                raise SystemExit(f"REJECTED: {query_id} references excluded source {source_id}")
    if not 8 <= len(ids) <= 10:
        raise SystemExit("REJECTED: dev probe must contain 8-10 entries")
    print(f"Validated {len(ids)} dev-only retrieval probes; no fixed-test IDs or excluded sources found.")


if __name__ == "__main__":
    main()
