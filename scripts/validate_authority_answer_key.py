"""Validate the source-first Week 6 authority answer-key structure."""

from __future__ import annotations

import json
from pathlib import Path

from legal_xai.answer_key import is_test_split_case, load_test_split_ids


def main() -> None:
    schema = json.loads(Path("config/authority_answer_key_schema.json").read_text(encoding="utf-8"))
    key = json.loads(Path("answer_key/authority_answer_key.json").read_text(encoding="utf-8"))
    test_case_ids = load_test_split_ids("corpus/ildc/single_test.parquet")
    if key["schema_version"] != schema["version"]:
        raise ValueError("Answer-key schema version mismatch")
    entries = key["entries"]
    if not entries:
        raise ValueError("The answer key must contain at least one independently verified entry")
    evaluation_case_ids: set[str] = set()
    dev_example_case_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        missing = [field for field in schema["required_entry_fields"] if not entry.get(field)]
        if missing:
            raise ValueError(f"Entry {index} is missing required fields: {missing}")
        if entry["relationship"] not in schema["allowed_relationships"]:
            raise ValueError(f"Entry {index} has an unsupported relationship")
        if entry["status"] not in schema["allowed_statuses"]:
            raise ValueError(f"Entry {index} has an unsupported status")
        if entry["independent_of_system_retrieval"] is not True:
            raise ValueError(f"Entry {index} is not independent of system retrieval")
        if not entry["query_source_url"].startswith("https://") or not entry["verification_source_url"].startswith("https://"):
            raise ValueError(f"Entry {index} lacks an HTTPS source URL")
        if entry["status"] == "evaluation":
            if not is_test_split_case(entry["query_case_id"], test_case_ids):
                raise ValueError(
                    f"Entry {index} is an evaluation entry but its query case is not in "
                    "the fixed ILDC test split"
                )
            evaluation_case_ids.add(entry["query_case_id"])
        else:
            dev_example_case_ids.add(entry["query_case_id"])

    if key["evaluation_target_test_cases"] != schema["evaluation_target_test_cases"]:
        raise ValueError("Evaluation target conflicts with the frozen schema")
    if key["evaluation_test_cases_complete"] != len(evaluation_case_ids):
        raise ValueError("Recorded evaluation-case count does not match evaluation entries")
    print(
        f"Validated {len(entries)} source-first authority entries: "
        f"{len(evaluation_case_ids)} evaluation test case(s) of "
        f"{key['evaluation_target_test_cases']} and {len(dev_example_case_ids)} "
        "development/example case(s)."
    )


if __name__ == "__main__":
    main()
