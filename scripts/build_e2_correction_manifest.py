"""Record the discarded and corrected E2 runs without overwriting either."""
from __future__ import annotations
import json
from pathlib import Path

def main() -> None:
    old = json.loads(Path("artifacts/e2_baseline_results.json").read_text(encoding="utf-8"))
    corrected = json.loads(Path("artifacts/e2_chunk_pool_results.json").read_text(encoding="utf-8"))
    result = {
        "E2_256_token_prefix": {"status": "Discarded", "reason": "256-token cap; 1491/1503 (99.20%) eligible test inputs were truncated.", "test_metrics": old["test_metrics"]},
        "E2_chunk_and_pool": {"status": "Corrected", "reason": "512-token windows with 50-token overlap; every eligible test document is represented by one or more windows.", "primary_pooling": "mean logits before softmax", "test_metrics": corrected["test_document_metrics"], "coverage": corrected["test_document_metrics"]["window_coverage"]},
    }
    Path("artifacts/e2_correction_manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    Path("artifacts/e2_correction_manifest.md").write_text("# E2 correction manifest\n\n## Discarded: 256-token cap, 99.2% truncated\n\nThe original prefix-only E2 result is retained for traceability but is not the accepted E2 result. Test accuracy: **{:.4f}**; macro F1: **{:.4f}**.\n\n## Corrected: chunk-and-pool\n\nThe accepted E2 run uses overlapping 512-token windows (50-token overlap) and mean-pooled logits before softmax. All {}/{} eligible test documents are covered. Test accuracy: **{:.4f}**; macro F1: **{:.4f}**. Majority-vote comparison: accuracy **{:.4f}**, macro F1 **{:.4f}**.\n".format(old["test_metrics"]["accuracy"], old["test_metrics"]["macro_f1"], result["E2_chunk_and_pool"]["coverage"]["fully_covered_documents"], result["E2_chunk_and_pool"]["coverage"]["eligible_documents"], corrected["test_document_metrics"]["mean_logits"]["accuracy"], corrected["test_document_metrics"]["mean_logits"]["macro_f1"], corrected["test_document_metrics"]["majority_vote"]["accuracy"], corrected["test_document_metrics"]["majority_vote"]["macro_f1"]), encoding="utf-8")
if __name__ == "__main__": main()
