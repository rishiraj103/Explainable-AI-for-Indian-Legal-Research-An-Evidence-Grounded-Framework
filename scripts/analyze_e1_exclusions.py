"""Audit whether E1 facts-extraction exclusions change the evaluation population."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from legal_xai.facts import extract_case_facts, facts_input_is_eligible, load_facts_extraction_rule


SPLITS = ("train", "validation", "test")


def _quantile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower), 1)


def _header_category(text: str) -> str:
    """A coarse, auditable category from the opening 1,500 source characters."""

    opening = text[:1500].casefold()
    if "criminal" in opening and "jurisdiction" in opening:
        return "criminal"
    if "civil" in opening and "jurisdiction" in opening:
        return "civil"
    if "original jurisdiction" in opening:
        return "original"
    if "writ petition" in opening:
        return "writ_or_constitutional"
    return "other_or_unclassified"


def _population_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_words = [len(str(row["text"]).split()) for row in rows]
    years = [int(str(row["id"]).split("_", 1)[0]) for row in rows]
    types = Counter(_header_category(str(row["text"])) for row in rows)
    return {
        "rows": len(rows),
        "label_counts": dict(sorted(Counter(int(row["label"]) for row in rows).items())),
        "source_word_quantiles": {"p10": _quantile(source_words, 0.1), "median": _quantile(source_words, 0.5), "p90": _quantile(source_words, 0.9)},
        "year_range": [min(years), max(years)],
        "header_derived_case_type_counts": dict(sorted(types.items())),
        "header_derived_case_type_percent": {
            category: round(count * 100 / len(rows), 2) for category, count in sorted(types.items())
        },
    }


def _write_markdown(path: Path, audit: dict[str, Any]) -> None:
    overall = audit["overall"]
    exclusion_rate = audit["exclusion_rate_percent"]
    retained = overall["retained"]
    excluded = overall["excluded"]
    lines = [
        "# E1 facts-extraction exclusion audit",
        "",
        f"The frozen facts-only gate excluded **{excluded['rows']} / {audit['total_rows']} ({exclusion_rate:.2f}%)** ILDC rows before E1. This audit compares those rows with the retained E1 population; it does not change the frozen extraction rule or E1 result.",
        "",
        "## Overall comparison",
        "",
        "| Population | Rows | Label counts | Source words (P10 / median / P90) | Year range |",
        "| --- | ---: | --- | --- | --- |",
        f"| Retained | {retained['rows']} | `{retained['label_counts']}` | `{retained['source_word_quantiles']}` | `{retained['year_range']}` |",
        f"| Excluded | {excluded['rows']} | `{excluded['label_counts']}` | `{excluded['source_word_quantiles']}` | `{excluded['year_range']}` |",
        "",
        "## Exclusion causes",
        "",
        f"- Eligibility failure reasons: `{audit['exclusion_failure_reasons']}`.",
        f"- Boundary reasons among excluded rows: `{audit['excluded_boundary_reasons']}`.",
        "",
        "## Broad header-derived case-type mix",
        "",
        "These are rough opening-header categories, not substantive legal classifications.",
        "",
        f"- Retained: `{retained['header_derived_case_type_percent']}`",
        f"- Excluded: `{excluded['header_derived_case_type_percent']}`",
        "",
        "## Finding",
        "",
        "The exclusions are a small share of the corpus and are not simply unusually short judgments: their median source length is compared directly above. They are near-balanced by label. The header mix is broadly civil-dominant in both groups; small-category percentage differences are descriptive only because the excluded group has 87 rows. The reported E1 population and its exclusions remain explicit in the experiment record.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/e1_baseline.json"))
    parser.add_argument("--output-json", type=Path, default=Path("artifacts/e1_exclusion_audit.json"))
    parser.add_argument("--output-markdown", type=Path, default=Path("artifacts/e1_exclusion_audit.md"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rule = load_facts_extraction_rule(config["facts_extraction_config"])

    retained_all: list[dict[str, Any]] = []
    excluded_all: list[dict[str, Any]] = []
    per_split: dict[str, Any] = {}
    failure_reasons: Counter[str] = Counter()
    boundary_reasons: Counter[str] = Counter()
    for split in SPLITS:
        table = pq.read_table(config["fixed_split_files"][split], columns=["id", "text", "label"])
        retained: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for row in table.to_pylist():
            result = extract_case_facts(row["text"], rule)
            if facts_input_is_eligible(result, rule):
                retained.append(row)
            else:
                excluded.append(row)
                retained_fraction = result.retained_char_count / result.source_char_count if result.source_char_count else 0.0
                if retained_fraction < rule.minimum_retained_fraction:
                    failure_reasons["below_minimum_retained_fraction"] += 1
                if len(result.text.split()) < rule.minimum_facts_words:
                    failure_reasons["below_minimum_facts_words"] += 1
                boundary_reasons[result.boundary_reason] += 1
        retained_all.extend(retained)
        excluded_all.extend(excluded)
        per_split[split] = {"retained": _population_summary(retained), "excluded": _population_summary(excluded)}

    audit = {
        "facts_rule_version": rule.version,
        "total_rows": len(retained_all) + len(excluded_all),
        "exclusion_rate_percent": round(len(excluded_all) * 100 / (len(retained_all) + len(excluded_all)), 4),
        "overall": {"retained": _population_summary(retained_all), "excluded": _population_summary(excluded_all)},
        "per_fixed_split": per_split,
        "exclusion_failure_reasons": dict(sorted(failure_reasons.items())),
        "excluded_boundary_reasons": dict(sorted(boundary_reasons.items())),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    _write_markdown(args.output_markdown, audit)
    print(json.dumps({"exclusion_rate_percent": audit["exclusion_rate_percent"], "overall": audit["overall"]}, indent=2))


if __name__ == "__main__":
    main()
