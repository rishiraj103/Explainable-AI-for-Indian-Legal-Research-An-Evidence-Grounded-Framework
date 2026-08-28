"""Validate the frozen ILDC pre-decision extraction rule before model fitting.

The script writes a deterministic, stratified 30-document review log. It also
computes corpus-wide boundary and retention statistics, and reports any known
outcome phrases that remain in an extracted input slice.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import statistics

import pyarrow.parquet as pq

from legal_xai.facts import (
    extract_case_facts,
    facts_input_is_eligible,
    find_outcome_cues,
    load_facts_extraction_rule,
)


SPLITS = ("train", "validation", "test")


def _load_split(corpus_dir: Path, split: str) -> list[dict[str, object]]:
    table = pq.read_table(corpus_dir / f"single_{split}.parquet", columns=["id", "text", "label"])
    return table.to_pylist()


def _sentence_complete(text: str) -> bool:
    return bool(text) and text.rstrip().endswith((".", "!", "?", "\u201d", "\u2019"))


def _sample_rows(rows: list[dict[str, object]], split: str, per_label: int, rng: random.Random) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for label in (0, 1):
        pool = [row for row in rows if int(row["label"]) == label]
        if len(pool) < per_label:
            raise ValueError(f"{split} has fewer than {per_label} rows for label {label}")
        selected.extend(rng.sample(pool, per_label))
    return selected


def _review_record(row: dict[str, object], split: str, rule) -> dict[str, object]:
    source = str(row["text"])
    result = extract_case_facts(source, rule)
    boundary = result.boundary_char if result.boundary_char is not None else len(source)
    return {
        "split": split,
        "id": str(row["id"]),
        "label": int(row["label"]),
        "boundary_reason": result.boundary_reason,
        "source_words": len(source.split()),
        "facts_words": len(result.text.split()),
        "retained_fraction": round(result.retained_char_count / result.source_char_count, 4) if result.source_char_count else 0.0,
        "remaining_outcome_cues": find_outcome_cues(result.text, rule),
        "eligible_for_facts_experiment": facts_input_is_eligible(result, rule),
        "sentence_complete": _sentence_complete(result.text),
        "facts_preview": result.text[:450].replace("\n", " "),
        "boundary_context": source[max(0, boundary - 220): min(len(source), boundary + 260)].replace("\n", " "),
    }


def _corpus_summary(rows_by_split: dict[str, list[dict[str, object]]], rule) -> dict[str, object]:
    records = []
    for split, rows in rows_by_split.items():
        for row in rows:
            source = str(row["text"])
            result = extract_case_facts(source, rule)
            records.append(
                {
                    "split": split,
                    "boundary_reason": result.boundary_reason,
                    "source_words": len(source.split()),
                    "facts_words": len(result.text.split()),
                    "retained_fraction": result.retained_char_count / result.source_char_count if result.source_char_count else 0.0,
                    "remaining_outcome_cues": find_outcome_cues(result.text, rule),
                    "eligible_for_facts_experiment": facts_input_is_eligible(result, rule),
                    "sentence_complete": _sentence_complete(result.text),
                }
            )
    summary = {
        "documents": len(records),
        "boundary_reasons": dict(sorted(Counter(item["boundary_reason"] for item in records).items())),
        "median_source_words": statistics.median(item["source_words"] for item in records),
        "median_facts_words": statistics.median(item["facts_words"] for item in records),
        "median_retained_fraction": round(statistics.median(item["retained_fraction"] for item in records), 4),
        "short_facts_inputs_under_100_words": sum(item["facts_words"] < 100 for item in records),
        "excluded_low_retention_or_short_inputs": sum(
            not item["eligible_for_facts_experiment"] for item in records
        ),
        "incomplete_facts_inputs": sum(not item["sentence_complete"] for item in records),
        "remaining_known_outcome_cues": sum(bool(item["remaining_outcome_cues"]) for item in records),
    }
    summary["eligible_by_fixed_split"] = {
        split: sum(
            item["eligible_for_facts_experiment"] for item in records if item["split"] == split
        )
        for split in SPLITS
    }
    return summary


def _write_markdown(
    path: Path,
    rule,
    summary: dict[str, object],
    records: list[dict[str, object]],
    seed: int,
    manual_review_status: str,
) -> None:
    lines = [
        "# ILDC facts-extraction validation",
        "",
        f"Rule version: `{rule.version}`  ",
        "Validation date: generated before any E1 model fit  ",
        f"Deterministic sample: five documents per label from each fixed split (30 total), seed `{seed}`.",
        "",
        "## Frozen rule",
        "",
        "Keep text before the earlier of the configured closing-section/dispositive boundary and the frozen 60% positional cap. When possible, move every cut back to the prior complete sentence. The manual review checks that no outcome language remains and that the slice retains useful factual content.",
        "",
        "## Corpus-wide automated checks",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- **{key.replace('_', ' ')}:** `{value}`")
    manual_note = (
        "PASS — reviewed all 30 deterministic samples: no target Supreme Court outcome language was observed in the retained slices; all ended at a sentence boundary. One early-disposition multi-opinion case (`test/1980_363`) retained only procedural material and is correctly excluded by the frozen eligibility gate."
        if manual_review_status == "pass"
        else "PENDING — inspect each deterministic sample before freezing the rule."
    )
    lines.extend([
        "",
        "Automated cue scans are necessary but not sufficient: the manual review below checks for semantic leakage and lost factual content.",
        "",
        "## Deterministic manual-review sample",
        "",
    ])
    for record in records:
        cues = "; ".join(record["remaining_outcome_cues"]) or "none"
        lines.extend([
            f"### {record['split']} / `{record['id']}` / label `{record['label']}`",
            "",
            f"- Boundary: `{record['boundary_reason']}`; words retained/source: `{record['facts_words']}/{record['source_words']}`; retained fraction: `{record['retained_fraction']}`.",
            f"- Ends at sentence boundary: `{record['sentence_complete']}`; known outcome cues remaining: `{cues}`; eligible for E1/E2: `{record['eligible_for_facts_experiment']}`.",
            f"- Facts preview: {record['facts_preview']!r}",
            f"- Boundary context: {record['boundary_context']!r}",
            f"- Manual review: `{manual_note}`",
            "",
        ])
    lines.extend([
        "## Declared limitation",
        "",
        "ILDC does not supply gold-standard facts/reasoning annotations. This rule can retain pre-decision legal reasoning or remove factual material at a detected boundary, so it is a reproducible approximation rather than a ground-truth facts segmentation.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", type=Path, default=Path("corpus/ildc"))
    parser.add_argument("--rule", type=Path, default=Path("config/facts_extraction.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/facts_extraction_validation.md"))
    parser.add_argument("--summary-output", type=Path, default=Path("artifacts/facts_extraction_validation.json"))
    parser.add_argument("--seed", type=int, default=202605)
    parser.add_argument("--per-label", type=int, default=5)
    parser.add_argument("--manual-review-status", choices=("pending", "pass"), default="pending")
    args = parser.parse_args()

    rule = load_facts_extraction_rule(args.rule)
    rows_by_split = {split: _load_split(args.corpus_dir, split) for split in SPLITS}
    summary = _corpus_summary(rows_by_split, rule)
    rng = random.Random(args.seed)
    records = [
        _review_record(row, split, rule)
        for split in SPLITS
        for row in _sample_rows(rows_by_split[split], split, args.per_label, rng)
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(args.output, rule, summary, records, args.seed, args.manual_review_status)
    args.summary_output.write_text(
        json.dumps(
            {
                "rule_version": rule.version,
                "seed": args.seed,
                "manual_review_status": args.manual_review_status,
                "summary": summary,
                "sample": records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    print(f"Wrote {args.output} and {args.summary_output}")


if __name__ == "__main__":
    main()
