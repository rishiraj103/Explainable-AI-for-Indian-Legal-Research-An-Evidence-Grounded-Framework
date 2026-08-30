"""Replace the stale E1/E2 comparison with the accepted corrected E2 run."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    e1 = json.loads(Path("artifacts/e1_baseline_results.json").read_text(encoding="utf-8"))
    e2 = json.loads(Path("artifacts/e2_chunk_pool_results.json").read_text(encoding="utf-8"))
    discarded = json.loads(Path("artifacts/e2_correction_manifest.json").read_text(encoding="utf-8"))["E2_256_token_prefix"]
    e1_metrics = e1["test_metrics"]
    majority = e1["majority_class_baseline"]
    mean = e2["test_document_metrics"]["mean_logits"]
    vote = e2["test_document_metrics"]["majority_vote"]
    payload = {
        "comparison_version": "e1-e2-corrected-chunk-pool-v1",
        "shared_input": "ildc-predecision-facts-v1 and the same eligible fixed-split cases; no retrieval/evidence lookup.",
        "majority_class_baseline": majority,
        "E1": e1_metrics,
        "E2_discarded_256_prefix": discarded,
        "E2_corrected": {"mean_logits_primary": mean, "majority_vote_secondary": vote},
        "accuracy_difference_vs_E1": {
            "mean_logits": mean["accuracy"] - e1_metrics["accuracy"],
            "majority_vote": vote["accuracy"] - e1_metrics["accuracy"],
        },
        "macro_f1_difference_vs_E1": {
            "mean_logits": mean["macro_f1"] - e1_metrics["macro_f1"],
            "majority_vote": vote["macro_f1"] - e1_metrics["macro_f1"],
        },
        "conclusion": "Corrected InLegalBERT trails E1 under both pooling reports, while both exceed the 50.17% majority-class baseline. The discarded 256-token result is retained only for traceability.",
    }
    Path("artifacts/e1_e2_comparison.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Locked E1–E2 Comparison (Corrected E2)", "",
        "Both experiments use `ildc-predecision-facts-v1`, the same eligible fixed ILDC split cases, and no retrieval/evidence lookup.",
        "",
        "| Test metric | E1: TF-IDF + Logistic Regression | E2: InLegalBERT mean logits (primary) | E2: majority vote (comparison) |",
        "| --- | ---: | ---: | ---: |",
        f"| Accuracy | {e1_metrics['accuracy']:.4f} | {mean['accuracy']:.4f} | {vote['accuracy']:.4f} |",
        f"| Macro F1 | {e1_metrics['macro_f1']:.4f} | {mean['macro_f1']:.4f} | {vote['macro_f1']:.4f} |",
        "",
        f"Majority-class baseline accuracy: `{majority['accuracy']:.4f}`. Corrected E2 trails E1 by `{abs(mean['accuracy'] - e1_metrics['accuracy']) * 100:.2f}` percentage points (mean logits) and `{abs(vote['accuracy'] - e1_metrics['accuracy']) * 100:.2f}` points (majority vote).",
        "",
        "## Discarded prior result", "",
        f"The old 256-token prefix E2 result (accuracy `{discarded['test_metrics']['accuracy']:.4f}`, macro F1 `{discarded['test_metrics']['macro_f1']:.4f}`) is **discarded — truncation bug**: 1,491/1,503 eligible test inputs (99.20%) were truncated. It must not be compared with E1 as a final E2 result.",
        "",
        "## Conclusion", "",
        payload["conclusion"],
        "",
    ]
    Path("artifacts/e1_e2_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"E1_accuracy": e1_metrics["accuracy"], "E2_mean_accuracy": mean["accuracy"]}, indent=2))


if __name__ == "__main__":
    main()
