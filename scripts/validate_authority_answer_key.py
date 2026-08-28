"""Validate the source-first Week 6 authority answer-key structure."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    schema = json.loads(Path("config/authority_answer_key_schema.json").read_text(encoding="utf-8"))
    key = json.loads(Path("answer_key/authority_answer_key.json").read_text(encoding="utf-8"))
    if key["schema_version"] != schema["version"]:
        raise ValueError("Answer-key schema version mismatch")
    entries = key["entries"]
    if not entries:
        raise ValueError("The answer key must contain at least one independently verified entry")
    for index, entry in enumerate(entries, start=1):
        missing = [field for field in schema["required_entry_fields"] if not entry.get(field)]
        if missing:
            raise ValueError(f"Entry {index} is missing required fields: {missing}")
        if entry["relationship"] not in schema["allowed_relationships"]:
            raise ValueError(f"Entry {index} has an unsupported relationship")
        if entry["independent_of_system_retrieval"] is not True:
            raise ValueError(f"Entry {index} is not independent of system retrieval")
        if not entry["query_source_url"].startswith("https://") or not entry["verification_source_url"].startswith("https://"):
            raise ValueError(f"Entry {index} lacks an HTTPS source URL")
    print(f"Validated {len(entries)} source-first authority entries for {len(set(item['query_case_id'] for item in entries))} query case(s).")


if __name__ == "__main__":
    main()
