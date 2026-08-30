"""Run inference only from E2's frozen best checkpoint and save document predictions.

The cached 512-token windows are the exact fixed Week 6 inputs.  No training,
validation selection, checkpoint update, or tokenizer rebuild occurs here.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from transformers import AutoModelForSequenceClassification


def metrics(labels: list[int], predictions: list[int]) -> dict[str, object]:
    return {
        "accuracy": round(float(accuracy_score(labels, predictions)), 6),
        "macro_f1": round(float(f1_score(labels, predictions, average="macro", zero_division=0)), 6),
        "class_0_f1": round(float(f1_score(labels, predictions, pos_label=0, zero_division=0)), 6),
        "class_1_f1": round(float(f1_score(labels, predictions, pos_label=1, zero_division=0)), 6),
        "confusion_matrix_labels": [0, 1],
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
    }


def pool(logits: np.ndarray, document_indices: np.ndarray, labels: list[int]) -> tuple[list[int], list[int]]:
    mean_predictions: list[int] = []
    vote_predictions: list[int] = []
    for document_index in range(len(labels)):
        window_logits = logits[document_indices == document_index]
        if not len(window_logits):
            raise ValueError(f"document {document_index} has no cached windows")
        mean_predictions.append(int(np.argmax(window_logits.mean(axis=0))))
        votes = Counter(np.argmax(window_logits, axis=1).tolist())
        # Frozen tie policy: lower label wins.
        vote_predictions.append(min(label for label, count in votes.items() if count == max(votes.values())))
    return mean_predictions, vote_predictions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("artifacts/e2_chunk_pool_cache/test"))
    parser.add_argument("--checkpoint", type=Path, default=Path("artifacts/e2_chunk_pool_checkpoints_cached/checkpoint-6318"))
    parser.add_argument("--recorded-result", type=Path, default=Path("artifacts/e2_chunk_pool_results.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/e2_test_predictions.json"))
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("E2 inference requires the frozen CUDA execution environment")
    metadata = json.loads((args.cache_dir / "metadata.json").read_text(encoding="utf-8"))
    ids = [str(value) for value in metadata["eligible_case_ids"]]
    labels = [int(value) for value in metadata["document_labels"]]
    input_ids = np.load(args.cache_dir / "input_ids.npy", mmap_mode="r")
    attention_mask = np.load(args.cache_dir / "attention_mask.npy", mmap_mode="r")
    token_type_ids = np.load(args.cache_dir / "token_type_ids.npy", mmap_mode="r")
    document_indices = np.load(args.cache_dir / "document_indices.npy", mmap_mode="r")
    if not (len(ids) == len(labels) == int(document_indices.max()) + 1):
        raise ValueError("cached document metadata does not align with cached windows")

    model = AutoModelForSequenceClassification.from_pretrained(args.checkpoint).cuda().eval()
    logits: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, len(input_ids), args.batch_size):
            end = min(start + args.batch_size, len(input_ids))
            batch = {
                "input_ids": torch.as_tensor(np.asarray(input_ids[start:end]), device="cuda", dtype=torch.long),
                "attention_mask": torch.as_tensor(np.asarray(attention_mask[start:end]), device="cuda", dtype=torch.long),
                "token_type_ids": torch.as_tensor(np.asarray(token_type_ids[start:end]), device="cuda", dtype=torch.long),
            }
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                logits.append(model(**batch).logits.float().cpu().numpy())
    all_logits = np.concatenate(logits, axis=0)
    mean_predictions, vote_predictions = pool(all_logits, np.asarray(document_indices), labels)
    mean_metrics = metrics(labels, mean_predictions)
    vote_metrics = metrics(labels, vote_predictions)
    recorded = json.loads(args.recorded_result.read_text(encoding="utf-8"))["test_document_metrics"]
    for name, observed, expected in (
        ("mean_logits", mean_metrics, recorded["mean_logits"]),
        ("majority_vote", vote_metrics, recorded["majority_vote"]),
    ):
        for field in ("accuracy", "macro_f1", "class_0_f1", "class_1_f1", "confusion_matrix"):
            if observed[field] != expected[field]:
                raise RuntimeError(
                    f"E2 {name} inference does not exactly reproduce {field}: "
                    f"got {observed[field]!r}, expected {expected[field]!r}. No predictions were written."
                )
    payload = {
        "artifact_version": "e2-test-predictions-frozen-checkpoint-v1",
        "method": "Inference only from frozen checkpoint-6318 using the frozen cached 512-token/50-overlap test windows and original pooling rules.",
        "checkpoint": str(args.checkpoint).replace("\\", "/"),
        "mean_logits_metrics": mean_metrics,
        "majority_vote_metrics": vote_metrics,
        "records": [
            {
                "case_id": case_id, "true_label": label,
                "E2_mean_logits_prediction": mean_prediction,
                "E2_majority_vote_prediction": vote_prediction,
            }
            for case_id, label, mean_prediction, vote_prediction in zip(ids, labels, mean_predictions, vote_predictions)
        ],
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "exact_reproduction_confirmed", "mean_logits": mean_metrics, "records": len(ids)}, indent=2))


if __name__ == "__main__":
    main()
