"""Audit frozen facts-only inputs against InLegalBERT's token limits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from transformers import AutoConfig, AutoTokenizer

from legal_xai.facts import extract_case_facts, facts_input_is_eligible, load_facts_extraction_rule


SPLITS = ("train", "validation", "test")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _percentile(sorted_values: list[int], percentile: float) -> int:
    if not sorted_values:
        raise ValueError("Cannot calculate a percentile from no values.")
    position = (len(sorted_values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    return round(sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower))


def _summarize(lengths: list[int], limits: tuple[int, ...]) -> dict[str, Any]:
    ordered = sorted(lengths)
    summary: dict[str, Any] = {
        "eligible_cases": len(ordered),
        "min": ordered[0],
        "p25": _percentile(ordered, 0.25),
        "median": _percentile(ordered, 0.50),
        "p75": _percentile(ordered, 0.75),
        "p90": _percentile(ordered, 0.90),
        "p95": _percentile(ordered, 0.95),
        "p99": _percentile(ordered, 0.99),
        "max": ordered[-1],
        "mean": round(sum(ordered) / len(ordered), 2),
    }
    for limit in limits:
        exceeded = sum(length > limit for length in ordered)
        summary[f"exceeds_{limit}"] = exceeded
        summary[f"exceeds_{limit}_rate"] = round(exceeded / len(ordered), 6)
    return summary


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    rows = "\n".join(
        "| {split} | {eligible_cases} | {median} | {p90} | {p95} | {p99} | {max} | {exceeds_256} ({exceeds_256_rate:.2%}) | {exceeds_512} ({exceeds_512_rate:.2%}) |".format(
            split=split.title(), **summary
        )
        for split, summary in result["splits"].items()
    )
    path.write_text(
        "\n".join(
            [
                "# E2 facts-input token-length audit",
                "",
                f"Tokenizer: `{result['model']['id']}` at revision `{result['model']['revision']}`. Token counts exclude special tokens, so the actual encoded sequence is two tokens longer for the standard BERT pair markers.",
                f"InLegalBERT configuration supports `{result['model']['max_position_embeddings']}` positions. The originally run E2 configuration used a `{result['implemented_max_length']}`-token limit.",
                "",
                "| Split | Eligible cases | Median | P90 | P95 | P99 | Max | >256 tokens | >512 tokens |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
                rows,
                "",
                "## Audit interpretation",
                "",
                result["interpretation"],
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/e2_baseline.json"))
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/e2_input_length_audit.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("artifacts/e2_input_length_audit.md"))
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    rule = load_facts_extraction_rule(config["facts_extraction_config"])
    tokenizer = AutoTokenizer.from_pretrained(config["model"]["id"], revision=config["model"]["revision"])
    model_config = AutoConfig.from_pretrained(config["model"]["id"], revision=config["model"]["revision"])
    limits = (config["input"]["max_length"], 512)
    summaries: dict[str, dict[str, Any]] = {}
    for split in SPLITS:
        source_path = Path(config["fixed_split_files"][split])
        texts: list[str] = []
        for row in pq.read_table(source_path, columns=["text"]).to_pylist():
            extracted = extract_case_facts(row["text"], rule)
            if facts_input_is_eligible(extracted, rule):
                texts.append(extracted.text)
        tokenized = tokenizer(texts, add_special_tokens=False, truncation=False, padding=False)
        summaries[split] = _summarize([len(ids) for ids in tokenized["input_ids"]], limits)
        summaries[split]["source_sha256"] = _sha256(source_path)

    test = summaries["test"]
    result = {
        "audit": "facts-only input lengths before E2 tokenization truncation",
        "facts_rule_version": rule.version,
        "model": {
            "id": config["model"]["id"],
            "revision": config["model"]["revision"],
            "max_position_embeddings": model_config.max_position_embeddings,
        },
        "implemented_max_length": config["input"]["max_length"],
        "splits": summaries,
        "interpretation": (
            f"On the locked test population, {test['exceeds_256']} of {test['eligible_cases']} inputs "
            f"({test['exceeds_256_rate']:.2%}) exceed the implemented 256-token limit; "
            f"{test['exceeds_512']} ({test['exceeds_512_rate']:.2%}) exceed 512 tokens. "
            "The 256-token cap is therefore an explicit implementation limitation to evaluate before accepting E2 as a model-only comparison."
        ),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_markdown(args.output_markdown, result)
    print(json.dumps({split: {key: value for key, value in summary.items() if key in {"eligible_cases", "median", "p95", "max", "exceeds_256", "exceeds_256_rate", "exceeds_512", "exceeds_512_rate"}} for split, summary in summaries.items()}, indent=2))


if __name__ == "__main__":
    main()
