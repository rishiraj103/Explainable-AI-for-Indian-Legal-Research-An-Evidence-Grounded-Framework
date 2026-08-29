"""Utilities that enforce the frozen ILDC test-split answer-key population."""

from __future__ import annotations

from pathlib import Path
import json

import pyarrow.parquet as pq


def load_split_ids(path: str | Path) -> set[str]:
    """Return normalized ILDC Single case IDs from one fixed split file."""
    table = pq.read_table(Path(path), columns=["id"])
    return {str(case_id).strip() for case_id in table.column("id").to_pylist()}


def load_test_split_ids(path: str | Path) -> set[str]:
    """Return the normalized case IDs in the fixed ILDC Single test split."""
    return load_split_ids(path)


def is_test_split_case(case_id: str, test_case_ids: set[str]) -> bool:
    """Whether a candidate is eligible to enter the evaluation answer-key pool."""
    return str(case_id).strip() in test_case_ids


def is_dev_only_case(
    case_id: str, train_case_ids: set[str], validation_case_ids: set[str], test_case_ids: set[str]
) -> bool:
    """Whether a probe belongs to train/validation and is outside the test split."""
    normalized = str(case_id).strip()
    return normalized in (train_case_ids | validation_case_ids) and normalized not in test_case_ids


def mirror_source_quality_status(
    source_id: str, cleaning_record_path: str | Path = "corpus/ecourts/cleaning_record.json"
) -> str:
    """Return the Week 3 quality status for an eCourts-mirror source document."""
    record = json.loads(Path(cleaning_record_path).read_text(encoding="utf-8"))
    if source_id in set(record["repair_source_ids"]):
        for year in record["years"]:
            for outcome in year["repair_outcomes"]:
                if outcome["source_id"] == source_id and outcome["status"] == "excluded_residual_low_quality":
                    return "excluded_low_quality"
        return "OCR-repaired"
    return "native-text"
