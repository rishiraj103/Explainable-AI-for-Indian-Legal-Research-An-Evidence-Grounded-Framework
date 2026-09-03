"""Validate and summarize a completed Week 13 review response.

The script is deliberately read-only with respect to the frozen model,
retrieval, answer-key, and explanation artifacts.  It maps display-order
ratings back to the structured and unstructured presentations before reporting
descriptive results.  It does not turn an author self-review into an
independent human-review metric.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ("source_clarity", "source_finding_ease", "appropriate_trust", "limits_clear")
PARITY_AUDIT = ROOT / "artifacts/week13_rq3_ablation_parity.json"


def sample_orders() -> dict[str, str]:
    """Read the final packet's fixed order instead of duplicating it in code."""
    audit = json.loads(PARITY_AUDIT.read_text(encoding="utf-8"))
    return {row["case_id"]: row["presentation_order"] for row in audit["per_case"]}


def read_response(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("review_version") != "week13-human-explanation-review-v2-rq3-ablation":
        raise ValueError("unexpected review_version")
    reviewer = payload.get("reviewer", {})
    if reviewer.get("outside_reviewer") not in (True, False):
        raise ValueError("reviewer.outside_reviewer must be true or false")
    if not reviewer.get("review_date"):
        raise ValueError("reviewer.review_date is required")
    samples = sample_orders()
    ratings = payload.get("ratings")
    if not isinstance(ratings, list) or len(ratings) != len(samples):
        raise ValueError(f"exactly {len(samples)} case ratings are required")
    if {row.get("case_id") for row in ratings} != set(samples):
        raise ValueError("ratings must cover the fixed packet cases exactly once")

    for row in ratings:
        case_id = row["case_id"]
        if row.get("presentation_order") != samples[case_id]:
            raise ValueError(f"presentation order changed for {case_id}")
        for display in ("display_1", "display_2"):
            values = row.get(display, {})
            for criterion in CRITERIA:
                value = values.get(criterion)
                if not isinstance(value, int) or not 1 <= value <= 5:
                    raise ValueError(f"{case_id} {display} {criterion} must be an integer from 1 to 5")
        if not str(row.get("comparison_preference", "")).strip():
            raise ValueError(f"comparison_preference is required for {case_id}")
    return payload


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    samples = sample_orders()
    totals = {presentation: {criterion: [] for criterion in CRITERIA} for presentation in ("structured", "unstructured")}
    preferences: Counter[str] = Counter()
    for row in payload["ratings"]:
        display_to_presentation = (
            {"display_1": "structured", "display_2": "unstructured"}
            if row["presentation_order"] == "structured_first"
            else {"display_1": "unstructured", "display_2": "structured"}
        )
        for display, presentation in display_to_presentation.items():
            for criterion in CRITERIA:
                totals[presentation][criterion].append(row[display][criterion])
        preference = str(row["comparison_preference"]).strip().lower()
        if preference not in {"structured", "unstructured", "no preference"}:
            raise ValueError("comparison_preference must be structured, unstructured, or no preference")
        preferences[preference] += 1
    return {
        "review_version": payload["review_version"],
        "reviewer_status": "independent_outside_reviewer" if payload["reviewer"]["outside_reviewer"] else "author_self_review_fallback",
        "reviewer": payload["reviewer"],
        "sample": {"case_count": len(payload["ratings"]), "case_ids": list(samples)},
        "mean_ratings": {
            presentation: {criterion: sum(values) / len(values) for criterion, values in measures.items()}
            for presentation, measures in totals.items()
        },
        "comparative_preferences": {key: preferences[key] for key in ("structured", "unstructured", "no preference")},
        "qualitative_feedback": [
            {
                "case_id": row["case_id"],
                "display_1_notes": row["display_1"]["notes"],
                "display_2_notes": row["display_2"]["notes"],
                "comparison_notes": row["comparison_notes"],
            }
            for row in payload["ratings"]
        ],
        "limitations": [
            "This is a seven-case, non-random paired usability sample, not a legal-correctness evaluation.",
            "Ratings are descriptive and are not statistically generalizable.",
            "If reviewer_status is author_self_review_fallback, the result is not independent human-review evidence and must not be reported as such.",
        ],
        "derivation": "Read-only summary of a completed response; no system output, frozen setting, model, retrieval run, or answer key was changed.",
    }


def markdown(summary: dict[str, Any]) -> str:
    reviewer = summary["reviewer"]
    lines = [
        "# Week 13 Explanation-Quality Review Summary",
        "",
        "## Reviewer status and scope",
        "",
        f"Status: `{summary['reviewer_status']}`. Reviewer background: {reviewer.get('role_or_background') or 'not supplied'}. Review date: {reviewer['review_date']}.",
        "",
        f"The review compares the frozen structured and unstructured presentations for {summary['sample']['case_count']} fixed cases. It measures perceived explanation quality, not legal correctness.",
        "",
        "## Descriptive ratings",
        "",
        "| Presentation | Source clarity | Source-finding ease | Appropriate trust | Limits clear |",
        "|---|---:|---:|---:|---:|",
    ]
    for presentation in ("structured", "unstructured"):
        measures = summary["mean_ratings"][presentation]
        lines.append(
            f"| {presentation.title()} | {measures['source_clarity']:.2f} | {measures['source_finding_ease']:.2f} | {measures['appropriate_trust']:.2f} | {measures['limits_clear']:.2f} |"
        )
    prefs = summary["comparative_preferences"]
    lines.extend([
        "",
        f"Comparative preference counts: structured {prefs['structured']}/{summary['sample']['case_count']}; unstructured {prefs['unstructured']}/{summary['sample']['case_count']}; no preference {prefs['no preference']}/{summary['sample']['case_count']}.",
        "",
        "## Qualitative feedback",
        "",
    ])
    for item in summary["qualitative_feedback"]:
        lines.extend([
            f"### Case `{item['case_id']}`",
            "",
            f"Display 1: {item['display_1_notes'] or 'No note supplied.'}",
            "",
            f"Display 2: {item['display_2_notes'] or 'No note supplied.'}",
            "",
            f"Comparison: {item['comparison_notes'] or 'No note supplied.'}",
            "",
        ])
    lines.extend(["## Limitations", "", *[f"- {item}" for item in summary["limitations"]], ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("response", type=Path, help="completed JSON response based on week13_review_response_template.json")
    parser.add_argument("--json-output", type=Path, default=ROOT / "artifacts/week13_review_summary.json")
    parser.add_argument("--markdown-output", type=Path, default=ROOT / "artifacts/week13_review_summary.md")
    args = parser.parse_args()
    summary = summarize(read_response(args.response))
    args.json_output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown(summary), encoding="utf-8")
    print(json.dumps({"status": "review_summary_written", "reviewer_status": summary["reviewer_status"]}, indent=2))


if __name__ == "__main__":
    main()
