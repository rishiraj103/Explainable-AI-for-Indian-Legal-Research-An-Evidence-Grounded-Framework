"""Run a small, reproducible CPU feasibility check for legal-language models.

This is a Week 2 environment check, not a legal-answering system. It verifies
that a masked-language model loads locally and can complete representative
Indian-legal-domain sentences without relying on an external inference API.
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import UTC, datetime
from pathlib import Path

import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer


DEFAULT_MODELS = [
    "law-ai/InLegalBERT",
    "nlpaueb/legal-bert-small-uncased",
]

PROMPTS = [
    "The appeal is hereby [MASK].",
    "The petitioner was given an opportunity of [MASK].",
]


def top_tokens(
    model: AutoModelForMaskedLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    device: torch.device,
) -> list[dict[str, float | str]]:
    encoded = tokenizer(prompt, return_tensors="pt")
    mask_positions = (encoded["input_ids"] == tokenizer.mask_token_id).nonzero(as_tuple=False)
    if len(mask_positions) != 1:
        raise ValueError(f"Prompt must contain exactly one mask token: {prompt!r}")

    encoded = {name: tensor.to(device) for name, tensor in encoded.items()}
    with torch.inference_mode():
        logits = model(**encoded).logits[0, mask_positions[0, 1]]

    probabilities = torch.softmax(logits, dim=-1)
    values, indices = torch.topk(probabilities, k=5)
    return [
        {
            "token": tokenizer.decode([token_id]).strip(),
            "probability": round(float(probability), 6),
        }
        for probability, token_id in zip(values.tolist(), indices.tolist(), strict=True)
    ]


def test_model(model_name: str) -> dict[str, object]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForMaskedLM.from_pretrained(model_name).to(device)
    model.eval()
    load_seconds = round(time.perf_counter() - started, 3)

    outputs = []
    for prompt in PROMPTS:
        inference_started = time.perf_counter()
        predictions = top_tokens(model, tokenizer, prompt, device)
        outputs.append(
            {
                "prompt": prompt,
                "top_predictions": predictions,
                "inference_seconds": round(time.perf_counter() - inference_started, 3),
            }
        )

    result: dict[str, object] = {
        "model": model_name,
        "status": "passed",
        "device": str(device),
        "load_seconds": load_seconds,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "outputs": outputs,
    }
    if device.type == "cuda":
        result["peak_gpu_memory_mb"] = round(torch.cuda.max_memory_allocated(device) / (1024**2), 2)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--output", type=Path, default=Path("artifacts/model-feasibility.json"))
    args = parser.parse_args()

    report: dict[str, object] = {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "models": [],
    }

    for model_name in args.models:
        try:
            result = test_model(model_name)
        except Exception as error:  # Capture a model-specific failure in the research record.
            result = {"model": model_name, "status": "failed", "error": repr(error)}
        report["models"].append(result)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    failures = [result for result in report["models"] if result["status"] != "passed"]
    if failures:
        raise SystemExit("One or more model feasibility checks failed; inspect the JSON report.")


if __name__ == "__main__":
    main()
