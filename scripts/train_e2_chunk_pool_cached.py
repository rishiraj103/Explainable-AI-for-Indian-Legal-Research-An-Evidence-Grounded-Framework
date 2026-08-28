"""Run corrected E2 from memory-mapped chunk windows rather than RAM tensors."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pyarrow
import pyarrow.parquet as pq
import sklearn
import torch
from torch.utils.data import Dataset
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments, set_seed

from train_e2_chunk_pool import _id_digest, _pool_predictions, _sha256, _write_markdown


class CachedWindows(Dataset):
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.input_ids = np.load(directory / "input_ids.npy", mmap_mode="r")
        self.attention_mask = np.load(directory / "attention_mask.npy", mmap_mode="r")
        self.token_type_ids = np.load(directory / "token_type_ids.npy", mmap_mode="r")
        self.labels = np.load(directory / "window_labels.npy", mmap_mode="r")
        self.document_indices = np.load(directory / "document_indices.npy", mmap_mode="r")

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        return {
            "input_ids": torch.tensor(self.input_ids[index], dtype=torch.long),
            "attention_mask": torch.tensor(self.attention_mask[index], dtype=torch.long),
            "token_type_ids": torch.tensor(self.token_type_ids[index], dtype=torch.long),
            "labels": torch.tensor(self.labels[index], dtype=torch.long),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/e2_chunk_pool.json"))
    parser.add_argument("--cache-dir", type=Path, default=Path("artifacts/e2_chunk_pool_cache"))
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/e2_chunk_pool_results.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("artifacts/e2_chunk_pool_results.md"))
    parser.add_argument("--checkpoints", type=Path, default=Path("artifacts/e2_chunk_pool_checkpoints_cached"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    settings = config["training"]
    set_seed(settings["seed"])
    torch.backends.cuda.matmul.allow_tf32 = False
    metadata = {split: json.loads((args.cache_dir / split / "metadata.json").read_text(encoding="utf-8")) for split in ("train", "validation", "test")}
    datasets = {split: CachedWindows(args.cache_dir / split) for split in metadata}
    split_details = {}
    for split, details in metadata.items():
        source = Path(details["source_path"])
        split_details[split] = {
            "source_path": str(source), "source_sha256": _sha256(source),
            "source_rows": pq.ParquetFile(source).metadata.num_rows,
            "eligible_rows": details["eligible_documents"],
            "excluded_rows": pq.ParquetFile(source).metadata.num_rows - details["eligible_documents"],
            "eligible_id_sha256": _id_digest(details["eligible_case_ids"]),
            "label_counts": dict(sorted(Counter(details["document_labels"]).items())),
            "window_count": details["window_count"],
            "fully_covered_documents": details["fully_covered_documents"],
            "fully_covered_document_rate": details["fully_covered_document_rate"],
            "windows_per_document_median": int(np.median(np.bincount(datasets[split].document_indices))),
        }

    def validation_metrics(prediction):
        pooled = _pool_predictions(prediction.predictions, datasets["validation"].document_indices.tolist(), metadata["validation"]["document_labels"])
        return {"mean_logit_accuracy": pooled["mean_logits"]["accuracy"], "mean_logit_macro_f1": pooled["mean_logits"]["macro_f1"], "majority_vote_accuracy": pooled["majority_vote"]["accuracy"], "majority_vote_macro_f1": pooled["majority_vote"]["macro_f1"]}

    model = AutoModelForSequenceClassification.from_pretrained(config["model"]["id"], revision=config["model"]["revision"], num_labels=2, ignore_mismatched_sizes=True)
    model.gradient_checkpointing_enable(); model.config.use_cache = False
    training_args = TrainingArguments(output_dir=str(args.checkpoints), overwrite_output_dir=True, num_train_epochs=settings["num_train_epochs"], learning_rate=settings["learning_rate"], weight_decay=settings["weight_decay"], warmup_ratio=settings["warmup_ratio"], per_device_train_batch_size=settings["per_device_train_batch_size"], per_device_eval_batch_size=settings["per_device_eval_batch_size"], gradient_accumulation_steps=settings["gradient_accumulation_steps"], gradient_checkpointing=True, fp16=True, optim=settings["optim"], eval_strategy="epoch", save_strategy="epoch", save_total_limit=1, save_only_model=True, load_best_model_at_end=True, metric_for_best_model="mean_logit_accuracy", greater_is_better=True, logging_strategy="steps", logging_steps=100, report_to=[], seed=settings["seed"], dataloader_num_workers=0)
    trainer = Trainer(model=model, args=training_args, train_dataset=datasets["train"], eval_dataset=datasets["validation"], compute_metrics=validation_metrics)
    trainer.train()
    prediction = trainer.predict(datasets["test"])
    test_metrics = _pool_predictions(prediction.predictions, datasets["test"].document_indices.tolist(), metadata["test"]["document_labels"])
    result = {"experiment": config["experiment"], "config_path": str(args.config), "config_sha256": _sha256(args.config), "model": config["model"], "facts_rule_version": "ildc-predecision-facts-v1", "facts_extraction_config_sha256": _sha256(Path(config["facts_extraction_config"])), "selection_protocol": config["selection_protocol"], "best_checkpoint": trainer.state.best_model_checkpoint, "best_validation_metric": trainer.state.best_metric, "splits": split_details, "input": config["input"], "training": settings, "test_document_metrics": test_metrics, "versions": {"python": sys.version, "platform": platform.platform(), "torch": torch.__version__, "cuda_available": torch.cuda.is_available(), "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "scikit_learn": sklearn.__version__, "pyarrow": pyarrow.__version__}, "model_weights_committed": False, "storage": "disk-backed NumPy memory-mapped windows"}
    args.output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_markdown(args.output_markdown, result)
    print(json.dumps({"best_validation_metric": result["best_validation_metric"], "test_document_metrics": test_metrics}, indent=2))

if __name__ == "__main__": main()
