"""Train and evaluate the frozen Week 5 E1 prediction baseline.

E1 consumes only the shared pre-decision input extracted by
``legal_xai.facts``. It selects the Logistic Regression regularization setting
on the supplied validation split, then performs one final test evaluation.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import sys
from typing import Any

import pyarrow
import pyarrow.parquet as pq
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from legal_xai.facts import extract_case_facts, facts_input_is_eligible, load_facts_extraction_rule


SPLITS = ("train", "validation", "test")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _id_digest(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def _load_eligible_split(path: Path, rule) -> tuple[list[str], list[str], list[int], list[str]]:
    table = pq.read_table(path, columns=["id", "text", "label"])
    ids: list[str] = []
    texts: list[str] = []
    labels: list[int] = []
    excluded_ids: list[str] = []
    for row in table.to_pylist():
        result = extract_case_facts(row["text"], rule)
        case_id = str(row["id"])
        if not facts_input_is_eligible(result, rule):
            excluded_ids.append(case_id)
            continue
        ids.append(case_id)
        texts.append(result.text)
        labels.append(int(row["label"]))
    return ids, texts, labels, excluded_ids


def _metrics(labels: list[int], predictions: list[int]) -> dict[str, Any]:
    matrix = confusion_matrix(labels, predictions, labels=[0, 1]).tolist()
    return {
        "accuracy": round(float(accuracy_score(labels, predictions)), 6),
        "macro_f1": round(float(f1_score(labels, predictions, average="macro", zero_division=0)), 6),
        "class_0_f1": round(float(f1_score(labels, predictions, pos_label=0, zero_division=0)), 6),
        "class_1_f1": round(float(f1_score(labels, predictions, pos_label=1, zero_division=0)), 6),
        "confusion_matrix_labels": [0, 1],
        "confusion_matrix": matrix,
    }


def _vectorizer(config: dict[str, Any]) -> TfidfVectorizer:
    settings = config["tfidf"]
    return TfidfVectorizer(
        lowercase=settings["lowercase"],
        strip_accents=settings["strip_accents"],
        ngram_range=tuple(settings["ngram_range"]),
        min_df=settings["min_df"],
        max_df=settings["max_df"],
        max_features=settings["max_features"],
        sublinear_tf=settings["sublinear_tf"],
        norm=settings["norm"],
    )


def _classifier(config: dict[str, Any], c_value: float) -> LogisticRegression:
    settings = config["logistic_regression"]
    return LogisticRegression(
        C=c_value,
        solver=settings["solver"],
        penalty=settings["penalty"],
        class_weight=settings["class_weight"],
        max_iter=settings["max_iter"],
        random_state=settings["random_state"],
    )


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    validation_rows = "\n".join(
        f"| {item['C']} | {item['accuracy']:.4f} | {item['macro_f1']:.4f} |"
        for item in result["validation_candidates"]
    )
    test = result["test_metrics"]
    split_rows = "\n".join(
        f"| {split} | {details['source_rows']} | {details['eligible_rows']} | {details['excluded_rows']} | `{details['eligible_id_sha256']}` |"
        for split, details in result["splits"].items()
    )
    path.write_text(
        "\n".join(
            [
                "# E1 TF-IDF + Logistic Regression baseline",
                "",
                f"Configuration: `{result['config_path']}` (SHA-256 `{result['config_sha256']}`)  ",
                f"Facts extractor: `{result['facts_rule_version']}`  ",
                "Test evaluation was run only after validation selected the locked hyperparameter.",
                "",
                "## Fixed split accounting",
                "",
                "| Split | Source rows | Eligible facts-only rows | Excluded low-retention/short rows | Eligible-ID SHA-256 |",
                "| --- | ---: | ---: | ---: | --- |",
                split_rows,
                "",
                "## Validation selection",
                "",
                "| C | Accuracy | Macro F1 |",
                "| ---: | ---: | ---: |",
                validation_rows,
                "",
                f"Selected `C={result['selected_C']}` by validation accuracy; ties use the smaller C.",
                "",
                "## Final test result",
                "",
                f"- Accuracy: **{test['accuracy']:.4f}**",
                f"- Macro F1: **{test['macro_f1']:.4f}**",
                f"- Class 0 F1: `{test['class_0_f1']:.4f}`; Class 1 F1: `{test['class_1_f1']:.4f}`.",
                f"- Confusion matrix (rows=true, columns=predicted; labels 0,1): `{test['confusion_matrix']}`.",
                "",
                "## Reproducibility and limitation",
                "",
                "The exact raw split-file and eligible-ID digests, package versions, seed, and all model settings are in the companion JSON. ILDC lacks gold-standard facts/reasoning boundaries; this frozen heuristic is a reproducible approximation and may retain legal reasoning or exclude material near a boundary.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/e1_baseline.json"))
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/e1_baseline_results.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("artifacts/e1_baseline_results.md"))
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    rule = load_facts_extraction_rule(config["facts_extraction_config"])
    split_data: dict[str, tuple[list[str], list[str], list[int], list[str]]] = {}
    split_details: dict[str, dict[str, Any]] = {}

    for split in SPLITS:
        path = Path(config["fixed_split_files"][split])
        ids, texts, labels, excluded_ids = _load_eligible_split(path, rule)
        split_data[split] = (ids, texts, labels, excluded_ids)
        split_details[split] = {
            "source_path": str(path),
            "source_sha256": _sha256(path),
            "source_rows": len(ids) + len(excluded_ids),
            "eligible_rows": len(ids),
            "excluded_rows": len(excluded_ids),
            "excluded_ids": excluded_ids,
            "eligible_id_sha256": _id_digest(ids),
            "label_counts": dict(sorted(Counter(labels).items())),
        }

    train_ids, train_texts, train_labels, _ = split_data["train"]
    _, validation_texts, validation_labels, _ = split_data["validation"]
    _, test_texts, test_labels, _ = split_data["test"]
    vectorizer = _vectorizer(config)
    train_features = vectorizer.fit_transform(train_texts)
    validation_features = vectorizer.transform(validation_texts)

    validation_candidates: list[dict[str, float]] = []
    for c_value in sorted(config["logistic_regression"]["candidate_C"]):
        classifier = _classifier(config, c_value)
        classifier.fit(train_features, train_labels)
        validation_metrics = _metrics(validation_labels, classifier.predict(validation_features).tolist())
        validation_candidates.append({"C": c_value, **validation_metrics})

    best = max(validation_candidates, key=lambda item: (item["accuracy"], -item["C"]))
    selected_c = best["C"]
    final_texts = train_texts + validation_texts
    final_labels = train_labels + validation_labels
    final_vectorizer = _vectorizer(config)
    final_features = final_vectorizer.fit_transform(final_texts)
    final_classifier = _classifier(config, selected_c)
    final_classifier.fit(final_features, final_labels)
    test_predictions = final_classifier.predict(final_vectorizer.transform(test_texts)).tolist()

    result = {
        "experiment": config["experiment"],
        "config_path": str(args.config),
        "config_sha256": _sha256(args.config),
        "facts_rule_version": rule.version,
        "facts_extraction_config_sha256": _sha256(Path(config["facts_extraction_config"])),
        "selection_protocol": config["selection_protocol"],
        "selected_C": selected_c,
        "validation_candidates": validation_candidates,
        "test_metrics": _metrics(test_labels, test_predictions),
        "splits": split_details,
        "final_fit": {"splits": ["train", "validation"], "rows": len(final_labels)},
        "versions": {
            "python": sys.version,
            "platform": platform.platform(),
            "scikit_learn": sklearn.__version__,
            "pyarrow": pyarrow.__version__,
        },
        "model_serialized": False,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_markdown(args.output_markdown, result)
    print(json.dumps({"selected_C": selected_c, "test_metrics": result["test_metrics"]}, indent=2))
    print(f"Wrote {args.output_json} and {args.output_markdown}")


if __name__ == "__main__":
    main()
