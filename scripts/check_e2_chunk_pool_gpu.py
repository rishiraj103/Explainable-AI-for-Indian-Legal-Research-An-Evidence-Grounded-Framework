"""Exercise one 512-token E2 training batch before a long GPU run."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def main() -> None:
    config = json.loads(Path("config/e2_chunk_pool.json").read_text(encoding="utf-8"))
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this capacity check.")
    tokenizer = AutoTokenizer.from_pretrained(config["model"]["id"], revision=config["model"]["revision"])
    model = AutoModelForSequenceClassification.from_pretrained(
        config["model"]["id"], revision=config["model"]["revision"], num_labels=2, ignore_mismatched_sizes=True
    ).cuda()
    model.gradient_checkpointing_enable()
    model.config.use_cache = False
    batch_size = config["training"]["per_device_train_batch_size"]
    encoded = tokenizer(
        ["legal facts " * 700] * batch_size,
        truncation=True,
        max_length=config["input"]["max_length"],
        padding="max_length",
        return_tensors="pt",
    )
    batch = {name: tensor.cuda() for name, tensor in encoded.items()}
    labels = torch.zeros(batch_size, dtype=torch.long, device="cuda")
    torch.cuda.reset_peak_memory_stats()
    model.train()
    model(**batch, labels=labels).loss.backward()
    peak_mib = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 1)
    total_mib = round(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024), 1)
    print(json.dumps({"batch_size": batch_size, "max_length": config["input"]["max_length"], "peak_allocated_mib": peak_mib, "gpu_total_mib": total_mib}, indent=2))


if __name__ == "__main__":
    main()
