"""Fine-tune the frozen InLegalBERT E2 baseline without retrieval evidence."""

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
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    set_seed,
)

from legal_xai.facts import extract_case_facts, facts_input_is_eligible, load_facts_extraction_rule


SPLITS = ("train", "validation", "test")


class TokenizedCases(Dataset):
    def __init__(self, encodings: dict[str, list[list[int]]], labels: list[int]) -> None:
        self.encodings = encodings
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        item = {name: torch.tensor(values[index]) for name, values in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[index], dtype=torch.long)
        return item


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
        extracted = extract_case_facts(row["text"], rule)
        case_id = str(row["id"])
        if not facts_input_is_eligible(extracted, rule):
            excluded_ids.append(case_id)
            continue
        ids.append(case_id)
        texts.append(extracted.text)
        labels.append(int(row["label"]))
    return ids, texts, labels, excluded_ids


def _metrics_from_arrays(labels: list[int], predictions: list[int]) -> dict[str, Any]:
    return {
        "accuracy": round(float(accuracy_score(labels, predictions)), 6),
        "macro_f1": round(float(f1_score(labels, predictions, average="macro", zero_division=0)), 6),
        "class_0_f1": round(float(f1_score(labels, predictions, pos_label=0, zero_division=0)), 6),
        "class_1_f1": round(float(f1_score(labels, predictions, pos_label=1, zero_division=0)), 6),
        "confusion_matrix_labels": [0, 1],
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
    }


def _compute_metrics(eval_prediction) -> dict[str, float]:
    logits, labels = eval_prediction
    predictions = logits.argmax(axis=-1)
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
    }


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    test = result["test_metrics"]
    split_rows = "\n".join(
        f"| {split} | {details['source_rows']} | {details['eligible_rows']} | {details['excluded_rows']} | `{details['eligible_id_sha256']}` |"
        for split, details in result["splits"].items()
    )
    path.write_text(
        "\n".join(
            [
                "# E2 InLegalBERT facts-only baseline",
                "",
                f"Model: `{result['model']['id']}` at revision `{result['model']['revision']}`  ",
                f"Facts extractor: `{result['facts_rule_version']}`; retrieval/evidence lookup: **not used**.  ",
                f"Best checkpoint was selected by validation accuracy: `{result['best_checkpoint']}`.",
                "",
                "## Fixed split accounting",
                "",
                "| Split | Source rows | Eligible facts-only rows | Excluded rows | Eligible-ID SHA-256 |",
                "| --- | ---: | ---: | ---: | --- |",
                split_rows,
                "",
                "## Final test result",
                "",
                f"- Accuracy: **{test['accuracy']:.4f}**",
                f"- Macro F1: **{test['macro_f1']:.4f}**",
                f"- Class 0 F1: `{test['class_0_f1']:.4f}`; Class 1 F1: `{test['class_1_f1']:.4f}`.",
                f"- Confusion matrix (rows=true, columns=predicted; labels 0,1): `{test['confusion_matrix']}`.",
                "",
                "## Comparison constraint",
                "",
                "E1 and E2 use the identical frozen facts-extraction function and eligible IDs. E2 tokenizes those inputs to a 256-token maximum because of the model architecture and 4 GB GPU limit; this truncation is recorded and should be considered when attributing any E1/E2 difference solely to model architecture.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/e2_baseline.json"))
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/e2_baseline_results.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("artifacts/e2_baseline_results.md"))
    parser.add_argument("--checkpoints", type=Path, default=Path("artifacts/e2_training_checkpoints"))
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    settings = config["training"]
    rule = load_facts_extraction_rule(config["facts_extraction_config"])
    set_seed(settings["seed"])
    torch.backends.cuda.matmul.allow_tf32 = False

    data: dict[str, tuple[list[str], list[str], list[int], list[str]]] = {}
    split_details: dict[str, dict[str, Any]] = {}
    for split in SPLITS:
        source_path = Path(config["fixed_split_files"][split])
        ids, texts, labels, excluded_ids = _load_eligible_split(source_path, rule)
        data[split] = (ids, texts, labels, excluded_ids)
        split_details[split] = {
            "source_path": str(source_path),
            "source_sha256": _sha256(source_path),
            "source_rows": len(ids) + len(excluded_ids),
            "eligible_rows": len(ids),
            "excluded_rows": len(excluded_ids),
            "excluded_ids": excluded_ids,
            "eligible_id_sha256": _id_digest(ids),
            "label_counts": dict(sorted(Counter(labels).items())),
        }

    tokenizer = AutoTokenizer.from_pretrained(config["model"]["id"], revision=config["model"]["revision"])
    tokenization = {
        "max_length": config["input"]["max_length"],
        "truncation": config["input"]["truncation"],
        "padding": config["input"]["padding"],
    }
    datasets: dict[str, TokenizedCases] = {}
    for split, (_, texts, labels, _) in data.items():
        datasets[split] = TokenizedCases(tokenizer(texts, **tokenization), labels)

    model = AutoModelForSequenceClassification.from_pretrained(
        config["model"]["id"],
        revision=config["model"]["revision"],
        num_labels=2,
        ignore_mismatched_sizes=True,
    )
    if settings["gradient_checkpointing"]:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    training_args = TrainingArguments(
        output_dir=str(args.checkpoints),
        overwrite_output_dir=True,
        num_train_epochs=settings["num_train_epochs"],
        learning_rate=settings["learning_rate"],
        weight_decay=settings["weight_decay"],
        warmup_ratio=settings["warmup_ratio"],
        per_device_train_batch_size=settings["per_device_train_batch_size"],
        per_device_eval_batch_size=settings["per_device_eval_batch_size"],
        gradient_accumulation_steps=settings["gradient_accumulation_steps"],
        gradient_checkpointing=settings["gradient_checkpointing"],
        fp16=settings["fp16"],
        optim=settings["optim"],
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        logging_strategy="steps",
        logging_steps=50,
        report_to=[],
        seed=settings["seed"],
        dataloader_num_workers=0,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        compute_metrics=_compute_metrics,
    )
    trainer.train()
    prediction = trainer.predict(datasets["test"])
    test_labels = data["test"][2]
    test_predictions = prediction.predictions.argmax(axis=-1).tolist()
    result = {
        "experiment": config["experiment"],
        "config_path": str(args.config),
        "config_sha256": _sha256(args.config),
        "model": config["model"],
        "facts_rule_version": rule.version,
        "facts_extraction_config_sha256": _sha256(Path(config["facts_extraction_config"])),
        "selection_protocol": config["selection_protocol"],
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "best_validation_metric": trainer.state.best_metric,
        "test_metrics": _metrics_from_arrays(test_labels, test_predictions),
        "splits": split_details,
        "tokenization": tokenization,
        "training": settings,
        "versions": {
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "transformers": __import__("transformers").__version__,
            "scikit_learn": sklearn.__version__,
            "pyarrow": pyarrow.__version__,
        },
        "model_weights_committed": False,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_markdown(args.output_markdown, result)
    print(json.dumps({"best_validation_metric": result["best_validation_metric"], "test_metrics": result["test_metrics"]}, indent=2))


if __name__ == "__main__":
    main()
