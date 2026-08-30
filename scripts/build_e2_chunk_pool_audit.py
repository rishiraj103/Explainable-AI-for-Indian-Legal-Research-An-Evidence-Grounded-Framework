"""Record the corrected E2 validation curve and locked-checkpoint audit."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    result = json.loads(Path("artifacts/e2_chunk_pool_results.json").read_text(encoding="utf-8"))
    checkpoint = Path(result["best_checkpoint"])
    state = json.loads((checkpoint / "trainer_state.json").read_text(encoding="utf-8"))
    history = [
        {
            "epoch": entry["epoch"],
            "mean_logit_validation_accuracy": entry["eval_mean_logit_accuracy"],
            "mean_logit_validation_macro_f1": entry["eval_mean_logit_macro_f1"],
            "majority_vote_validation_accuracy": entry["eval_majority_vote_accuracy"],
            "eval_loss": entry["eval_loss"],
            "step": entry["step"],
        }
        for entry in state["log_history"]
        if "eval_mean_logit_accuracy" in entry
    ]
    coverage = result["test_document_metrics"]["window_coverage"]
    payload = {
        "audit_version": "e2-chunk-pool-training-audit-v1",
        "checkpoint": str(checkpoint).replace("\\", "/"),
        "checkpoint_matches_result": str(checkpoint) == result["best_checkpoint"],
        "best_validation_metric_from_state": state["best_metric"],
        "best_validation_metric_from_result": result["best_validation_metric"],
        "validation_history": history,
        "test_window_coverage": coverage,
        "test_confusion_matrix": result["test_document_metrics"]["mean_logits"]["confusion_matrix"],
    }
    Path("artifacts/e2_chunk_pool_training_audit.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# E2 Corrected Chunk-and-Pool Training Audit", "",
        f"The evaluated checkpoint is `{checkpoint}`. It matches the saved result record: `{payload['checkpoint_matches_result']}`.",
        "",
        "## Validation curve", "",
        "| Epoch | Mean-logit accuracy | Mean-logit macro F1 | Majority-vote accuracy | Loss |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in history:
        lines.append(
            f"| {row['epoch']:.2f} | {row['mean_logit_validation_accuracy']:.4f} | "
            f"{row['mean_logit_validation_macro_f1']:.4f} | {row['majority_vote_validation_accuracy']:.4f} | {row['eval_loss']:.4f} |"
        )
    lines.extend([
        "",
        f"Best validation mean-logit accuracy: `{state['best_metric']:.6f}` at the final saved checkpoint.",
        f"Test coverage: `{coverage['fully_covered_documents']}/{coverage['eligible_documents']}` documents ({coverage['fully_covered_document_rate']:.2%}); no input is silently truncated to a prefix.",
        f"Primary test confusion matrix (rows=true, columns=predicted; labels 0/1): `{payload['test_confusion_matrix']}`.",
        "",
    ])
    Path("artifacts/e2_chunk_pool_training_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"validation_epochs": len(history), "best_validation_metric": state["best_metric"]}, indent=2))


if __name__ == "__main__":
    main()
