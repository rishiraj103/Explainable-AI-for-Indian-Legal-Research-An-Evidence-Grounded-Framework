"""Validate and record the corrected 30-case Week 11 evaluation reference set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from legal_xai.answer_key import load_test_split_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, default=Path("config/week11_evaluation_round.json"))
    parser.add_argument("--answer-key", type=Path, default=Path("answer_key/authority_answer_key.json"))
    parser.add_argument("--alignment-audit", type=Path, default=Path("artifacts/answer_key_alignment_audit_corrected.json"))
    parser.add_argument("--test-split", type=Path, default=Path("corpus/ildc/single_test.parquet"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/week11_answer_key_sanity_check.json"))
    args = parser.parse_args()

    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    answer_key = json.loads(args.answer_key.read_text(encoding="utf-8"))
    audit = json.loads(args.alignment_audit.read_text(encoding="utf-8"))
    entries = [entry for entry in answer_key["entries"] if entry.get("status") == "evaluation"]
    expected_count = int(freeze["reference_evidence_set"]["final_case_count"])
    if len(entries) != expected_count:
        raise ValueError(f"freeze declares {expected_count} evaluation entries, found {len(entries)}")
    case_ids = [str(entry["query_case_id"]) for entry in entries]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("evaluation answer key has duplicate query_case_id values")

    test_ids = load_test_split_ids(args.test_split)
    non_test = sorted(set(case_ids) - test_ids)
    if non_test:
        raise ValueError(f"evaluation cases outside fixed test split: {non_test}")

    audit_by_id = {str(row["query_case_id"]): row for row in audit["rows"]}
    missing_audit = sorted(set(case_ids) - set(audit_by_id))
    nonpassing = sorted(case_id for case_id in case_ids if audit_by_id[case_id].get("status") != "pass")
    if missing_audit or nonpassing:
        raise ValueError(f"alignment audit invalid: missing={missing_audit}, nonpassing={nonpassing}")

    collision_risk: list[dict[str, object]] = []
    for entry in entries:
        year = int(str(entry["query_decision_date"])[:4])
        if 1958 <= year <= 1993:
            row = audit_by_id[str(entry["query_case_id"])]
            collision_risk.append({
                "query_case_id": entry["query_case_id"],
                "query_decision_date": entry["query_decision_date"],
                "corrected_alignment_status": row["status"],
                "direct_six_token_phrase_matches": row["direct_six_token_phrase_matches"],
                "source_id": row["source_id"],
            })
    if any(row["corrected_alignment_status"] != "pass" for row in collision_risk):
        raise ValueError("a collision-risk-era case failed the corrected alignment gate")

    payload = {
        "artifact_version": "week11-answer-key-sanity-v1",
        "freeze_version": freeze["evaluation_round_version"],
        "summary": {
            "frozen_evaluation_cases": len(entries),
            "fixed_test_split_membership_pass": len(entries),
            "corrected_alignment_gate_pass": len(entries),
            "collision_risk_era_1958_1993_cases": len(collision_risk),
            "collision_risk_era_cases_all_individually_passed": True,
        },
        "evaluation_case_ids": case_ids,
        "collision_risk_era_cases": collision_risk,
        "method_note": "This validates the post-identifier-collision, content-driven alignment audit. The direct six-token phrase signal is the decisive content-alignment evidence; title/party overlap is a supplementary signal and is not substituted for content alignment.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
