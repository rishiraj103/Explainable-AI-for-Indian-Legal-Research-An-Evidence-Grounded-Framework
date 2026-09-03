"""Render Week 14 paper figures using only the finalized evidence inventory."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/figures"
INVENTORY = ROOT / "artifacts/week14_results_evidence_inventory.json"
FONT = "font-family='Arial, Helvetica, sans-serif'"
INK = "#202124"
MUTED = "#5f6368"
GRID = "#d7dce2"
BLUE = "#2962a3"
ORANGE = "#d97706"
GREEN = "#2e7d32"
RED = "#b3261e"


def esc(value: object) -> str:
    return html.escape(str(value))


def svg_open(title: str, width: int = 1100, height: int = 640) -> list[str]:
    return [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}' role='img' aria-labelledby='title desc'>",
        f"<title id='title'>{esc(title)}</title>",
        f"<desc id='desc'>{esc(title)}</desc>",
        "<rect width='100%' height='100%' fill='white'/>",
        f"<text x='55' y='44' {FONT} font-size='25' font-weight='700' fill='{INK}'>{esc(title)}</text>",
    ]


def text(x: float, y: float, value: str, size: int = 16, fill: str = INK, anchor: str = "start", weight: str = "400") -> str:
    return f"<text x='{x:.1f}' y='{y:.1f}' {FONT} font-size='{size}' font-weight='{weight}' fill='{fill}' text-anchor='{anchor}'>{esc(value)}</text>"


def line(x1: float, y1: float, x2: float, y2: float, color: str = GRID, width: float = 1) -> str:
    return f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{color}' stroke-width='{width}'/>"


def rect(x: float, y: float, width: float, height: float, fill: str) -> str:
    return f"<rect x='{x:.1f}' y='{y:.1f}' width='{width:.1f}' height='{height:.1f}' fill='{fill}'/>"


def write(name: str, lines: list[str]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text("\n".join([*lines, "</svg>"]) + "\n", encoding="utf-8")
    return path


def inventory_row(inventory: dict[str, Any], area: str) -> dict[str, Any]:
    return next(row for row in inventory["result_inventory"] if row["area"] == area)


def outcome_figure(inventory: dict[str, Any]) -> Path:
    measures = inventory_row(inventory, "Outcome prediction")["measures"]
    entries = [
        ("E1", measures["E1_accuracy"], measures["E1_macro_f1"]),
        ("E2 mean-logit", measures["E2_mean_logit_accuracy"], measures["E2_mean_logit_macro_f1"]),
        ("E2 majority-vote", measures["E2_majority_vote_accuracy"], measures["E2_majority_vote_macro_f1"]),
        ("Majority baseline", measures["majority_accuracy"], None),
    ]
    left, top, bottom, right = 100, 115, 555, 1050
    lines = svg_open("Outcome prediction on the frozen test population (n=1,503)")
    for tick in range(0, 8):
        value = tick / 10
        y = bottom - (bottom - top) * value / 0.7
        lines.extend([line(left, y, right, y), text(left - 12, y + 5, f"{value:.1f}", 13, MUTED, "end")])
    lines.extend([line(left, top, left, bottom, INK, 1.5), line(left, bottom, right, bottom, INK, 1.5), text(32, 335, "Score", 15, MUTED)])
    group_width = (right - left) / len(entries)
    bar_width = 58
    for index, (label, accuracy, f1) in enumerate(entries):
        center = left + group_width * (index + 0.5)
        for offset, value, color, tag in ((-34, accuracy, BLUE, "Accuracy"), (34, f1, ORANGE, "Macro F1")):
            if value is None:
                continue
            height = (bottom - top) * value / 0.7
            x = center + offset - bar_width / 2
            lines.extend([rect(x, bottom - height, bar_width, height, color), text(x + bar_width / 2, bottom - height - 9, f"{value:.3f}", 13, INK, "middle")])
        lines.extend([text(center, bottom + 27, label, 14, INK, "middle"), text(center, bottom + 47, "(accuracy only)" if f1 is None else "", 12, MUTED, "middle")])
    lines.extend([rect(730, 70, 16, 16, BLUE), text(754, 83, "Accuracy", 14), rect(850, 70, 16, 16, ORANGE), text(874, 83, "Macro F1", 14)])
    return write("week14_figure_a_outcome_prediction.svg", lines)


def retrieval_funnel_figure(inventory: dict[str, Any]) -> Path:
    measures = inventory_row(inventory, "Authority recovery and verified evidence")["measures"]
    selected = measures["retrieved_and_selected"]
    deferred = measures["retrieved_not_selected"]
    absent = measures["absent_at_k100"]
    total = selected + deferred + absent
    lines = svg_open("Expected-authority recovery funnel (n=30)")
    left, width = 130, 820
    rows = [
        ("Answer-key cases", total, total, BLUE, "30/30"),
        ("Found within k=100", selected + deferred, total, GREEN, f"{selected + deferred}/30 = Recall@100 0.50"),
        ("Found within top 5", selected, total, BLUE, f"{selected}/30 = Recall@5 0.40"),
    ]
    for index, (label, count, denominator, color, value) in enumerate(rows):
        y = 135 + index * 120
        bar_w = width * count / denominator
        lines.extend([text(left, y - 18, label, 18, INK, "start", "500"), rect(left, y, width, 58, "#edf1f5"), rect(left, y, bar_w, 58, color), text(left + bar_w + 16, y + 37, value, 17, INK)])
    y = 500
    lines.extend([
        text(left, y - 18, "Final k=100 breakdown", 18, INK, "start", "500"),
        rect(left, y, width * selected / total, 58, GREEN),
        rect(left + width * selected / total, y, width * deferred / total, 58, ORANGE),
        rect(left + width * (selected + deferred) / total, y, width * absent / total, 58, RED),
        text(left + width * selected / total / 2, y + 36, f"Selected {selected}", 14, "white", "middle", "500"),
        text(left + width * (selected + deferred / 2) / total, y + 36, f"Retrieved only {deferred}", 14, INK, "middle", "500"),
        text(left + width * ((selected + deferred) + absent / 2) / total, y + 36, f"Absent {absent}", 14, "white", "middle", "500"),
    ])
    return write("week14_figure_b_retrieval_funnel.svg", lines)


def investigation_figure(inventory: dict[str, Any]) -> Path:
    data = inventory["retrieval_investigation_visualization"]
    dev = data["development_probe_recall_at_100"]
    held = data["held_out_temporal_comparison"]
    lines = svg_open("Retrieval investigation: development repairs and held-out temporal test", 1200, 680)
    lines.extend([text(60, 82, "Development probe: Recall@100 (n=9)", 18, INK, "start", "500"), text(660, 82, "Held-out temporal comparison (n=30)", 18, INK, "start", "500")])
    for panel_left, panel_right in ((70, 565), (665, 1140)):
        top, bottom = 125, 530
        for tick in range(0, 11, 2):
            value = tick / 10
            y = bottom - (bottom - top) * value
            lines.extend([line(panel_left, y, panel_right, y), text(panel_left - 10, y + 5, f"{value:.1f}", 12, MUTED, "end")])
        lines.extend([line(panel_left, top, panel_left, bottom, INK, 1.5), line(panel_left, bottom, panel_right, bottom, INK, 1.5)])
    dev_width = 62
    for index, row in enumerate(dev):
        x = 125 + index * 110
        rate = row["numerator"] / row["denominator"]
        height = 405 * rate
        lines.extend([rect(x, 530 - height, dev_width, height, BLUE), text(x + dev_width / 2, 530 - height - 8, f"{row['numerator']}/{row['denominator']}", 13, INK, "middle")])
        words = row["stage"].replace("-", " ").split()
        lines.extend([text(x + dev_width / 2, 554, " ".join(words[:2]), 12, INK, "middle"), text(x + dev_width / 2, 572, " ".join(words[2:]), 12, INK, "middle")])
    held_group = 170
    for index, row in enumerate(held):
        center = 760 + index * 210
        for offset, value, color, label in ((-35, row["recall_at_5"], BLUE, "R@5"), (35, row["recall_at_100"], ORANGE, "R@100")):
            height = 405 * value
            x = center + offset - 28
            lines.extend([rect(x, 530 - height, 56, height, color), text(x + 28, 530 - height - 8, f"{round(value * row['denominator'])}/{row['denominator']}", 13, INK, "middle")])
        lines.extend([text(center, 554, row["stage"].split()[0], 12, INK, "middle"), text(center, 572, " ".join(row["stage"].split()[1:]), 12, INK, "middle")])
    lines.extend([
        rect(790, 610, 14, 14, BLUE), text(812, 622, "Recall@5", 13),
        rect(905, 610, 14, 14, ORANGE), text(927, 622, "Recall@100", 13),
        text(70, 642, "Panels use different frozen populations; the left panel is not a held-out Recall@5 trend.", 13, MUTED),
    ])
    return write("week14_figure_c_retrieval_investigation.svg", lines)


def integrity_figure(inventory: dict[str, Any]) -> Path:
    measures = inventory_row(inventory, "Authority recovery and verified evidence")["measures"]
    lines = svg_open("Displayed-evidence integrity under the final frozen configuration (n=30)", 1100, 475)
    headers = ["Check", "Result", "Interpretation"]
    rows = [
        ("Citation grounding", "150/150 passed", "Every displayed citation maps to supplied evidence"),
        ("Provenance validity", "150/150 passed", "Every displayed citation has persisted provenance"),
        ("Temporal violations", "0", "No same-year or later authority reached final output"),
        ("Unsupported claims", "0", "Controlled renderer made no unsupported evidence claim"),
    ]
    x = [55, 355, 575, 1045]
    y, row_h = 120, 65
    lines.extend([rect(x[0], y, x[-1] - x[0], row_h, BLUE)])
    for index, header in enumerate(headers):
        lines.append(text(x[index] + 12, y + 41, header, 16, "white", "start", "500"))
    for index, row in enumerate(rows, start=1):
        yy = y + index * row_h
        lines.extend([rect(x[0], yy, x[-1] - x[0], row_h, "#f7f9fb" if index % 2 else "#ffffff"), line(x[0], yy + row_h, x[-1], yy + row_h)])
        for cell, xx in zip(row, x):
            lines.append(text(xx + 12, yy + 41, cell, 15, INK))
    lines.append(text(55, 427, "All values are final E4 verification results; they assess displayed evidence, not expected-authority recovery.", 14, MUTED))
    return write("week14_figure_d_integrity_summary.svg", lines)


def review_figure(inventory: dict[str, Any]) -> Path:
    measures = inventory_row(inventory, "Explanation-format review")["measures"]
    structured = measures["structured_mean_ratings"]
    unstructured = measures["unstructured_mean_ratings"]
    fields = [("Source clarity", "source_clarity"), ("Source-finding ease", "source_finding_ease"), ("Appropriate trust", "appropriate_trust"), ("Limits clear", "limits_clear")]
    left, top, bottom, right = 105, 115, 540, 1050
    lines = svg_open("Explanation-format ratings: author self-review only (n=7)")
    for tick in range(0, 6):
        y = bottom - (bottom - top) * tick / 5
        lines.extend([line(left, y, right, y), text(left - 10, y + 5, str(tick), 13, MUTED, "end")])
    lines.extend([line(left, top, left, bottom, INK, 1.5), line(left, bottom, right, bottom, INK, 1.5), text(42, 330, "Mean rating (1–5)", 15, MUTED)])
    group = (right - left) / len(fields)
    for index, (label, key) in enumerate(fields):
        center = left + group * (index + 0.5)
        for offset, value, color in ((-34, structured[key], BLUE), (34, unstructured[key], ORANGE)):
            height = (bottom - top) * value / 5
            x = center + offset - 27
            lines.extend([rect(x, bottom - height, 54, height, color), text(x + 27, bottom - height - 8, f"{value:.2f}", 13, INK, "middle")])
        words = label.split()
        lines.extend([text(center, bottom + 28, " ".join(words[:2]), 13, INK, "middle"), text(center, bottom + 46, " ".join(words[2:]), 13, INK, "middle")])
    lines.extend([rect(690, 69, 16, 16, BLUE), text(714, 82, "Structured", 14), rect(825, 69, 16, 16, ORANGE), text(849, 82, "Unstructured", 14), text(105, 603, "Descriptive author self-review fallback; not independent human-review evidence.", 14, MUTED)])
    return write("week14_figure_e_explanation_review.svg", lines)


def captions() -> str:
    return """# Week 14 Figure Captions

**Figure A. Outcome-prediction comparison on the frozen eligible ILDC test population (n=1,503).** E1, corrected E2 mean-logit pooling, E2 majority-vote pooling, and the majority baseline are shown for accuracy and, where applicable, macro F1.

**Figure B. Expected-authority recovery funnel on the 30-case source-verified answer-key subset (n=30).** The final configuration finds 15/30 expected authorities within k=100, including 12/30 within the top five; the stacked final row separates 12 selected, three retrieved-but-unselected, and 15 absent authorities.

**Figure C. Retrieval investigation pathway.** The left panel shows development-probe Recall@100 (n=9) across the first-32-term query, salient-term query construction, coverage-qualified self-match repair, and the final pre-ranking consistency check. The right panel shows the held-out 30-case temporal comparison for Recall@5 and Recall@100. The panels remain separate because the salient-term and self-match fixes were development-probe interventions, while the pre-ranking temporal filter was tested on the frozen held-out cohort.

**Figure D. Displayed-evidence integrity under the final frozen configuration (n=30 queries; 150 displayed citations).** All displayed citations passed grounding and provenance checks, with zero temporal violations and zero unsupported claims; these verification outcomes are distinct from expected-authority recovery.

**Figure E. Explanation-format rubric means from the Week 13 author self-review fallback (n=7 paired cases).** Structured and unstructured presentations are compared across four perceived-quality dimensions. This is descriptive self-review evidence, not an independent human-review result.
"""


def chapter() -> str:
    results = (ROOT / "artifacts/week14_results_draft.md").read_text(encoding="utf-8")
    insertion = {
        "## Outcome prediction": "\n\n![Figure A. Outcome prediction comparison](figures/week14_figure_a_outcome_prediction.svg)\n\n*Figure A. Outcome-prediction comparison on the frozen eligible ILDC test population (n=1,503).*",
        "## Authority recovery, grounding, and temporal integrity": "\n\n![Figure B. Expected-authority recovery funnel](figures/week14_figure_b_retrieval_funnel.svg)\n\n*Figure B. Expected-authority recovery funnel on the 30-case source-verified answer-key subset (n=30).*\n\n![Figure D. Displayed-evidence integrity](figures/week14_figure_d_integrity_summary.svg)\n\n*Figure D. Displayed-evidence integrity under the final frozen configuration (n=30 queries; 150 displayed citations).*",
        "## Retrieval mechanism behind the final result": "\n\n![Figure C. Retrieval investigation](figures/week14_figure_c_retrieval_investigation.svg)\n\n*Figure C. Retrieval investigation pathway: development repairs and the held-out temporal comparison.*",
        "## Explanation-format observation": "\n\n![Figure E. Explanation-format review](figures/week14_figure_e_explanation_review.svg)\n\n*Figure E. Explanation-format rubric means from the Week 13 author self-review fallback (n=7 paired cases; not independent evidence).*",
    }
    for heading, figure in insertion.items():
        start = results.index(heading)
        paragraph_end = results.find("\n\n", start + len(heading))
        if paragraph_end == -1:
            paragraph_end = len(results)
        else:
            next_heading = results.find("\n## ", paragraph_end + 2)
            paragraph_end = len(results) if next_heading == -1 else next_heading
        results = results[:paragraph_end] + figure + "\n" + results[paragraph_end:]
    return "# Results Chapter Draft\n\n" + results.removeprefix("# Results Draft\n\n")


def main() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    paths = [
        outcome_figure(inventory),
        retrieval_funnel_figure(inventory),
        investigation_figure(inventory),
        integrity_figure(inventory),
        review_figure(inventory),
    ]
    (ROOT / "artifacts/week14_figure_captions.md").write_text(captions(), encoding="utf-8")
    (ROOT / "artifacts/results_chapter_draft.md").write_text(chapter(), encoding="utf-8")
    print(json.dumps({"figures": [str(path.relative_to(ROOT)).replace("\\", "/") for path in paths], "status": "paper_figures_and_results_chapter_written"}, indent=2))


if __name__ == "__main__":
    main()
