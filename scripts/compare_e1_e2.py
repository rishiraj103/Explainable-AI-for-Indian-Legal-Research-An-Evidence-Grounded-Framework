"""Create the locked, comparable E1/E2 test-result record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SPLITS = ("train", "validation", "test")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_same_facts_population(e1: dict[str, Any], e2: dict[str, Any]) -> None:
    if e1["facts_rule_version"] != e2["facts_rule_version"]:
        raise ValueError("E1 and E2 use different facts-extraction rule versions.")
    if e1["facts_extraction_config_sha256"] != e2["facts_extraction_config_sha256"]:
        raise ValueError("E1 and E2 use different facts-extraction configurations.")
    for split in SPLITS:
        e1_split = e1["splits"][split]
        e2_split = e2["splits"][split]
        if e1_split["eligible_id_sha256"] != e2_split["eligible_id_sha256"]:
            raise ValueError(f"E1 and E2 have different eligible IDs for {split}.")
        if e1_split["eligible_rows"] != e2_split["eligible_rows"]:
            raise ValueError(f"E1 and E2 have different eligible-row counts for {split}.")


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    e1 = result["experiments"]["E1"]
    e2 = result["experiments"]["E2"]
    delta = result["test_metric_deltas_e2_minus_e1"]
    path.write_text(
        "\n".join(
            [
                "# Locked E1–E2 comparison",
                "",
                "Both experiments used the frozen `ildc-predecision-facts-v1` extractor and exactly the same eligible cases in every fixed ILDC split. Neither used retrieval or evidence lookup.",
                "",
                "| Test metric | E1: TF-IDF + Logistic Regression | E2: InLegalBERT | E2 − E1 |",
                "| --- | ---: | ---: | ---: |",
                f"| Accuracy | {e1['accuracy']:.4f} | {e2['accuracy']:.4f} | {delta['accuracy']:+.4f} ({delta['accuracy_percentage_points']:+.2f} pp) |",
                f"| Macro F1 | {e1['macro_f1']:.4f} | {e2['macro_f1']:.4f} | {delta['macro_f1']:+.4f} |",
                "",
                "## Result",
                "",
                "E2 did **not** beat E1 under the frozen Week 6 settings. This is recorded as the outcome of the planned comparison, not tuned away. E1 remains the stronger facts-only baseline on this test evaluation.",
                "",
                "## Interpretation constraint",
                "",
                "The shared extractor and eligible-ID hashes make the included case population comparable. E2 nevertheless tokenizes inputs to 256 tokens for the InLegalBERT architecture and 4 GB GPU limit, while E1 consumes its full extracted text. That fixed input-length difference is a documented limitation when attributing the result only to model architecture.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--e1", type=Path, default=Path("artifacts/e1_baseline_results.json"))
    parser.add_argument("--e2", type=Path, default=Path("artifacts/e2_baseline_results.json"))
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/e1_e2_comparison.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("artifacts/e1_e2_comparison.md"))
    args = parser.parse_args()

    e1 = _load(args.e1)
    e2 = _load(args.e2)
    _ensure_same_facts_population(e1, e2)

    e1_metrics = e1["test_metrics"]
    e2_metrics = e2["test_metrics"]
    accuracy_delta = round(e2_metrics["accuracy"] - e1_metrics["accuracy"], 6)
    macro_f1_delta = round(e2_metrics["macro_f1"] - e1_metrics["macro_f1"], 6)
    result = {
        "comparison": "E2 minus E1 on the single locked test evaluation",
        "comparability": {
            "facts_rule_version": e1["facts_rule_version"],
            "facts_extraction_config_sha256": e1["facts_extraction_config_sha256"],
            "same_eligible_population_verified": True,
            "eligible_id_sha256_by_split": {
                split: e1["splits"][split]["eligible_id_sha256"] for split in SPLITS
            },
            "retrieval_or_evidence_lookup_used": False,
        },
        "experiments": {
            "E1": {
                "name": "TF-IDF + Logistic Regression",
                "accuracy": e1_metrics["accuracy"],
                "macro_f1": e1_metrics["macro_f1"],
            },
            "E2": {
                "name": "InLegalBERT",
                "accuracy": e2_metrics["accuracy"],
                "macro_f1": e2_metrics["macro_f1"],
                "max_input_tokens": e2["tokenization"]["max_length"],
            },
        },
        "test_metric_deltas_e2_minus_e1": {
            "accuracy": accuracy_delta,
            "accuracy_percentage_points": round(accuracy_delta * 100, 4),
            "macro_f1": macro_f1_delta,
        },
        "conclusion": "E2 did not beat E1 under the frozen Week 6 settings; no test-result-driven tuning was performed.",
        "known_comparison_limitation": "E2 uses a fixed 256-token model input, while E1 uses the full shared facts extraction output.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_markdown(args.output_markdown, result)
    print(json.dumps(result["test_metric_deltas_e2_minus_e1"], indent=2))


if __name__ == "__main__":
    main()
