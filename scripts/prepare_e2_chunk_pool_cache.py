"""Build disk-backed 512-token overflow windows for corrected E2 training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from transformers import AutoTokenizer

from legal_xai.facts import extract_case_facts, facts_input_is_eligible, load_facts_extraction_rule


SPLITS = ("train", "validation", "test")


def _eligible_cases(path: Path, rule):
    for batch in pq.ParquetFile(path).iter_batches(columns=["id", "text", "label"], batch_size=64):
        for row in batch.to_pylist():
            extracted = extract_case_facts(row["text"], rule)
            if facts_input_is_eligible(extracted, rule):
                yield str(row["id"]), extracted.text, int(row["label"])


def _window_starts(token_count: int, content_size: int, overlap: int) -> list[int]:
    if token_count <= content_size:
        return [0]
    starts = list(range(0, token_count - content_size + 1, content_size - overlap))
    final_start = token_count - content_size
    if starts[-1] != final_start:
        starts.append(final_start)
    return starts


def _write_split(split: str, source: Path, tokenizer, rule, settings: dict, cache_dir: Path) -> dict:
    documents = list(_eligible_cases(source, rule))
    content_size = settings["max_length"] - tokenizer.num_special_tokens_to_add(pair=False)
    document_token_ids = [tokenizer(text, add_special_tokens=False)["input_ids"] for _, text, _ in documents]
    windows_per_document = [_window_starts(len(ids), content_size, settings["overlap_tokens"]) for ids in document_token_ids]
    window_count = sum(len(starts) for starts in windows_per_document)
    split_dir = cache_dir / split
    split_dir.mkdir(parents=True, exist_ok=True)
    input_ids = np.lib.format.open_memmap(split_dir / "input_ids.npy", mode="w+", dtype=np.int32, shape=(window_count, settings["max_length"]))
    attention_mask = np.lib.format.open_memmap(split_dir / "attention_mask.npy", mode="w+", dtype=np.uint8, shape=(window_count, settings["max_length"]))
    token_type_ids = np.lib.format.open_memmap(split_dir / "token_type_ids.npy", mode="w+", dtype=np.uint8, shape=(window_count, settings["max_length"]))
    window_labels = np.lib.format.open_memmap(split_dir / "window_labels.npy", mode="w+", dtype=np.int64, shape=(window_count,))
    document_indices = np.lib.format.open_memmap(split_dir / "document_indices.npy", mode="w+", dtype=np.int32, shape=(window_count,))
    row = 0
    for document_index, ((case_id, _, label), ids, starts) in enumerate(zip(documents, document_token_ids, windows_per_document)):
        for start in starts:
            encoded = tokenizer.prepare_for_model(
                ids[start : start + content_size],
                add_special_tokens=True,
                padding="max_length",
                max_length=settings["max_length"],
                return_attention_mask=True,
                truncation=False,
            )
            input_ids[row] = encoded["input_ids"]
            attention_mask[row] = encoded["attention_mask"]
            token_type_ids[row] = encoded.get("token_type_ids", [0] * settings["max_length"])
            window_labels[row] = label
            document_indices[row] = document_index
            row += 1
    for array in (input_ids, attention_mask, token_type_ids, window_labels, document_indices):
        array.flush()
    metadata = {
        "split": split,
        "source_path": str(source),
        "eligible_case_ids": [case_id for case_id, _, _ in documents],
        "document_labels": [label for _, _, label in documents],
        "eligible_documents": len(documents),
        "window_count": window_count,
        "fully_covered_documents": len(documents),
        "fully_covered_document_rate": 1.0,
        "min_windows_per_document": min(map(len, windows_per_document)),
        "max_windows_per_document": max(map(len, windows_per_document)),
    }
    (split_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/e2_chunk_pool.json"))
    parser.add_argument("--cache-dir", type=Path, default=Path("artifacts/e2_chunk_pool_cache"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rule = load_facts_extraction_rule(config["facts_extraction_config"])
    tokenizer = AutoTokenizer.from_pretrained(config["model"]["id"], revision=config["model"]["revision"])
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        split: _write_split(split, Path(config["fixed_split_files"][split]), tokenizer, rule, config["input"], args.cache_dir)
        for split in SPLITS
    }
    (args.cache_dir / "cache_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({split: {"eligible_documents": value["eligible_documents"], "window_count": value["window_count"]} for split, value in summary.items()}, indent=2))


if __name__ == "__main__":
    main()
