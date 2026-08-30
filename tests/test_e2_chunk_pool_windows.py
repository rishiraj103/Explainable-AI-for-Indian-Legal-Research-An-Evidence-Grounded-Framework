"""Focused tests for E2's 512-token overflow-window contract."""

from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path("scripts/prepare_e2_chunk_pool_cache.py")
SPEC = importlib.util.spec_from_file_location("prepare_e2_chunk_pool_cache", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_long_input_produces_overlapping_512_token_windows_without_a_gap() -> None:
    max_length = 512
    special_tokens = 2
    content_size = max_length - special_tokens
    overlap = 50
    token_count = 1_200

    starts = MODULE._window_starts(token_count, content_size, overlap)
    spans = [(start, min(start + content_size, token_count)) for start in starts]

    assert len(starts) > 1
    assert spans[0][0] == 0
    assert spans[-1][1] == token_count
    assert all(right - left <= content_size for left, right in spans)
    assert all((right - left) + special_tokens <= max_length for left, right in spans)
    assert all(next_left <= right for (_, right), (next_left, _) in zip(spans, spans[1:]))
    assert spans[1][0] - spans[0][0] == content_size - overlap


def test_short_input_stays_in_one_bounded_window() -> None:
    assert MODULE._window_starts(token_count=300, content_size=510, overlap=50) == [0]
