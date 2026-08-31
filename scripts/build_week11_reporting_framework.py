"""Derive revised Week 11 reporting metrics from persisted frozen runs only."""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg

from load_provenance import DEFAULT_DATABASE_URL


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    evaluation = json.loads((ROOT / "artifacts/week11_initial_evaluation.json").read_text(encoding="utf-8"))
    runs = [row["retrieval_run_id"] for row in evaluation["per_case_records"]]
    cited = [(row["retrieval_run_id"], check["chunk_id"]) for row in evaluation["per_case_records"] for check in row["citation_checks"]]
    with psycopg.connect(os.getenv("LEGAL_XAI_DATABASE_URL", DEFAULT_DATABASE_URL)) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT temporal_status, count(*) FROM retrieval_results WHERE run_id = ANY(%s) "
            "GROUP BY temporal_status", (runs,)
        )
        candidate_statuses = dict(cursor.fetchall())
        cursor.execute(
            "SELECT rr.temporal_status, count(*) FROM retrieval_results rr "
            "JOIN unnest(%s::uuid[], %s::text[]) AS wanted(run_id, chunk_id) "
            "ON rr.run_id = wanted.run_id AND rr.chunk_id = wanted.chunk_id "
            "GROUP BY rr.temporal_status",
            ([item[0] for item in cited], [item[1] for item in cited]),
        )
        cited_statuses = dict(cursor.fetchall())
    candidate_total = sum(candidate_statuses.values())
    cited_total = sum(cited_statuses.values())
    future_candidates = candidate_statuses.get("ineligible", 0)
    future_cited = cited_statuses.get("ineligible", 0)
    payload = {
        "reporting_framework_version": "week11-temporal-reporting-v1",
        "scope": "The frozen 30-case answer-key cohort and its persisted Week 11 retrieval runs; no retrieval was rerun.",
        "temporal_metrics": {
            "FEER": {
                "definition": "future-ineligible retrieved candidates / all retrieved candidates logged after duplicate exclusion",
                "numerator": future_candidates,
                "denominator": candidate_total,
                "value": round(future_candidates / candidate_total, 6),
                "future_ineligible_status": "ineligible (candidate decision year later than query year)",
                "same_year_ambiguous_excluded_from_numerator": candidate_statuses.get("ambiguous_excluded", 0),
            },
            "FCER": {
                "definition": "future-ineligible final cited evidence items / all final cited evidence items",
                "numerator": future_cited,
                "denominator": cited_total,
                "value": round(future_cited / cited_total, 6),
            },
            "candidate_status_counts": candidate_statuses,
            "final_cited_status_counts": cited_statuses,
        },
        "prediction_delta_E4_minus_E3": {
            "value": None,
            "status": "not_defined",
            "reason": "The frozen E3/E4 systems do not emit outcome predictions; their shared evidence output is not a prediction label."
        },
    }
    (ROOT / "artifacts/week11_reporting_framework.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown = "\n".join([
        "# Week 11 Revised Reporting Framework",
        "",
        "## Temporal exposure and control metrics",
        "",
        "| Metric | Numerator | Denominator | Value |",
        "|---|---:|---:|---:|",
        f"| FEER: future-ineligible retrieved candidates / all retrieved candidates | {future_candidates} | {candidate_total} | {payload['temporal_metrics']['FEER']['value']:.6f} |",
        f"| FCER: future-ineligible final cited items / all final cited items | {future_cited} | {cited_total} | {payload['temporal_metrics']['FCER']['value']:.6f} |",
        "",
        f"The FEER numerator counts only `ineligible` later-year candidates. The {candidate_statuses.get('ambiguous_excluded', 0)} same-year candidates are retained as an explicitly ambiguous/excluded bucket rather than silently treated as future evidence. FCER is zero because final evidence selection admits only temporally eligible candidates.",
        "",
        "## E4-E3 prediction delta",
        "",
        "Prediction Delta (E4 - E3): **not defined**. Neither frozen system emits an outcome-prediction label, so a numeric prediction delta would be fabricated. E4 adds verification to E3's evidence presentation; it is not a second outcome classifier.",
        "",
        "## Operational definitions",
        "",
        "| Term | Implemented project definition |",
        "|---|---|",
        "| Temporal existence | An eCourts item has a parseable exact `decision_date`; candidates missing this metadata are excluded. ILDC query dates are available only at year granularity. |",
        "| Temporal effectiveness | The strict filter prevents later-year material from final citations: measured by FCER. Later-year material can remain visible in the candidate log, measured by FEER, for auditability. |",
        "| Temporal applicability | For an ILDC query with year Y, an eCourts precedent is eligible only when `precedent_decision_year < Y`. Same-year items are logged as `ambiguous_excluded`; later-year items are `ineligible`. |",
        "| Provenance validity | Each displayed evidence item must reproduce a corpus chunk's stable source ID, citation, decision date, court, PDF/page/character locator, exact passage text, and retrieval-run membership. |",
        "| Authority consistency | A final displayed authority matches the independently verified answer-key authority by stable source ID, normalized citation, or normalized title plus exact decision date. |",
        "| Future evidence exposure | FEER: the share of logged, post-duplicate-exclusion retrieval candidates that are later-year and therefore ineligible. It is distinct from FCER, which measures whether future evidence reached final cited output. |",
        "",
    ])
    (ROOT / "artifacts/week11_reporting_framework.md").write_text(markdown, encoding="utf-8")
    print(json.dumps(payload["temporal_metrics"], indent=2))


if __name__ == "__main__":
    main()
