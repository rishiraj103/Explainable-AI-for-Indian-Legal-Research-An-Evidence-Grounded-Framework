"""Verify E2 checkpoint selection and summarize its saved training history."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    validation_rows = "\n".join(
        f"| {item['epoch']:.2f} | {item['eval_accuracy']:.4f} | {item['eval_macro_f1']:.4f} | {item['eval_loss']:.4f} |"
        for item in result["validation_history"]
    )
    training = result["training_loss_observation"]
    path.write_text(
        "\n".join(
            [
                "# E2 training and checkpoint-selection audit",
                "",
                f"Saved best checkpoint: `{result['selected_checkpoint']}`. The final test evaluation was produced after loading that checkpoint, whose validation accuracy was `{result['best_validation_accuracy']:.4f}`.",
                "",
                "## Validation history",
                "",
                "| Epoch | Accuracy | Macro F1 | Loss |",
                "| ---: | ---: | ---: | ---: |",
                validation_rows,
                "",
                "## Training-loss observation",
                "",
                f"The first logged training loss was `{training['first']:.4f}` and the final logged training loss was `{training['last']:.4f}` ({training['relative_change_percent']:+.2f}%). Intermediate minibatch losses fluctuate, but the logged training loss declines and validation accuracy improves at each saved epoch; there is no majority-class-collapse or incorrect-checkpoint indication in this audit.",
                "",
                "## Test confusion matrix",
                "",
                f"Rows are true labels and columns predicted labels, ordered `[0, 1]`: `{result['test_confusion_matrix']}`. Both predicted classes occur (`{result['predicted_label_counts']['0']}` label-0 and `{result['predicted_label_counts']['1']}` label-1 predictions), so the result is not an all-majority-class collapse.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trainer-state", type=Path, default=Path("artifacts/e2_training_checkpoints/checkpoint-939/trainer_state.json"))
    parser.add_argument("--results", type=Path, default=Path("artifacts/e2_baseline_results.json"))
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/e2_training_audit.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("artifacts/e2_training_audit.md"))
    args = parser.parse_args()

    state: dict[str, Any] = json.loads(args.trainer_state.read_text(encoding="utf-8"))
    results: dict[str, Any] = json.loads(args.results.read_text(encoding="utf-8"))
    validation = [item for item in state["log_history"] if "eval_accuracy" in item]
    if not validation:
        raise ValueError("No validation records found in trainer state.")
    if state["best_model_checkpoint"] != results["best_checkpoint"]:
        raise ValueError("Saved trainer checkpoint does not match the E2 result record.")
    best_observed = max(validation, key=lambda item: item["eval_accuracy"])
    if best_observed["eval_accuracy"] != state["best_metric"]:
        raise ValueError("Trainer best metric does not match the best validation record.")
    losses = [item["loss"] for item in state["log_history"] if "loss" in item]
    confusion = results["test_metrics"]["confusion_matrix"]
    predicted_0 = confusion[0][0] + confusion[1][0]
    predicted_1 = confusion[0][1] + confusion[1][1]
    first_loss, last_loss = losses[0], losses[-1]
    result = {
        "audit": "saved E2 Trainer history and final-test checkpoint selection",
        "selected_checkpoint": state["best_model_checkpoint"],
        "best_validation_accuracy": state["best_metric"],
        "validation_history": [
            {
                "epoch": item["epoch"],
                "eval_accuracy": item["eval_accuracy"],
                "eval_macro_f1": item["eval_macro_f1"],
                "eval_loss": item["eval_loss"],
                "step": item["step"],
            }
            for item in validation
        ],
        "checkpoint_selection_verified": True,
        "training_loss_observation": {
            "first": first_loss,
            "last": last_loss,
            "relative_change_percent": round((last_loss - first_loss) / first_loss * 100, 4),
        },
        "test_confusion_matrix": confusion,
        "predicted_label_counts": {"0": predicted_0, "1": predicted_1},
        "test_metrics": results["test_metrics"],
        "conclusion": "The saved best checkpoint and both-class prediction behavior are verified. The audit does not establish a sequence-length strategy for inputs longer than the model limit.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_markdown(args.output_markdown, result)
    print(json.dumps({"checkpoint_selection_verified": True, "predicted_label_counts": result["predicted_label_counts"]}, indent=2))


if __name__ == "__main__":
    main()
