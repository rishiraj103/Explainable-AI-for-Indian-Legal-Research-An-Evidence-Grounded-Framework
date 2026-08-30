"""Deterministically reconstruct frozen E1 and persist its verified predictions.

This intentionally does not repeat validation selection: C=10.0 was frozen in
the original result and is refit once on the original train+validation inputs.
No artifact is written unless the recorded held-out metrics reproduce exactly.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib

from train_e1_baseline import _classifier, _load_eligible_split, _metrics, _vectorizer
from legal_xai.facts import load_facts_extraction_rule


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/e1_baseline.json"))
    parser.add_argument("--recorded-result", type=Path, default=Path("artifacts/e1_baseline_results.json"))
    parser.add_argument("--model-output", type=Path, default=Path("artifacts/e1_reconstructed_model.joblib"))
    parser.add_argument("--predictions-output", type=Path, default=Path("artifacts/e1_test_predictions.json"))
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    recorded = json.loads(args.recorded_result.read_text(encoding="utf-8"))
    if float(recorded["selected_C"]) != 10.0:
        raise ValueError("recorded E1 selection is not the expected frozen C=10.0")
    rule = load_facts_extraction_rule(config["facts_extraction_config"])
    train_ids, train_texts, train_labels, _ = _load_eligible_split(Path(config["fixed_split_files"]["train"]), rule)
    validation_ids, validation_texts, validation_labels, _ = _load_eligible_split(Path(config["fixed_split_files"]["validation"]), rule)
    test_ids, test_texts, test_labels, _ = _load_eligible_split(Path(config["fixed_split_files"]["test"]), rule)
    vectorizer = _vectorizer(config)
    features = vectorizer.fit_transform(train_texts + validation_texts)
    classifier = _classifier(config, 10.0)
    classifier.fit(features, train_labels + validation_labels)
    predictions = classifier.predict(vectorizer.transform(test_texts)).astype(int).tolist()
    metrics = _metrics(test_labels, predictions)
    expected = recorded["test_metrics"]
    for metric in ("accuracy", "macro_f1", "class_0_f1", "class_1_f1", "confusion_matrix"):
        if metrics[metric] != expected[metric]:
            raise RuntimeError(
                f"E1 reconstruction does not exactly reproduce {metric}: "
                f"got {metrics[metric]!r}, expected {expected[metric]!r}. No artifacts were written."
            )

    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "artifact_version": "e1-reconstructed-frozen-v1",
        "config": config,
        "selected_C": 10.0,
        "facts_rule_version": rule.version,
        "train_case_ids": train_ids,
        "validation_case_ids": validation_ids,
        "vectorizer": vectorizer,
        "classifier": classifier,
        "reproduction_metrics": metrics,
    }, args.model_output, compress=3)
    payload = {
        "artifact_version": "e1-test-predictions-reconstructed-v1",
        "method": "Deterministic refit using frozen C=10.0 on the original train+validation facts-only inputs; no validation search was rerun.",
        "recorded_metrics": expected,
        "reproduced_metrics": metrics,
        "model_artifact": str(args.model_output).replace("\\", "/"),
        "records": [
            {"case_id": case_id, "true_label": label, "E1_prediction": prediction}
            for case_id, label, prediction in zip(test_ids, test_labels, predictions)
        ],
    }
    args.predictions_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "exact_reproduction_confirmed", "metrics": metrics, "records": len(predictions)}, indent=2))


if __name__ == "__main__":
    main()
