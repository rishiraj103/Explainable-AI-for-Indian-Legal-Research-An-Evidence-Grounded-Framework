"""Utilities that enforce the frozen ILDC test-split answer-key population."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq


def load_test_split_ids(path: str | Path) -> set[str]:
    """Return the normalized case IDs in the fixed ILDC Single test split."""
    table = pq.read_table(Path(path), columns=["id"])
    return {str(case_id).strip() for case_id in table.column("id").to_pylist()}


def is_test_split_case(case_id: str, test_case_ids: set[str]) -> bool:
    """Whether a candidate is eligible to enter the evaluation answer-key pool."""
    return str(case_id).strip() in test_case_ids
