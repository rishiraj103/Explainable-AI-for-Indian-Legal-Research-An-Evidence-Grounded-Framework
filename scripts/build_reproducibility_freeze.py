"""Write the Week 10 reproducibility freeze from the actual checked-in inputs."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


FREEZE_VERSION = "week10-reproducibility-freeze-v1"
ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    return {
        "path": relative_path.replace("\\", "/"),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def split_record(split: str) -> dict[str, Any]:
    record = file_record(f"corpus/ildc/single_{split}.parquet")
    record["rows"] = pq.ParquetFile(ROOT / record["path"]).metadata.num_rows
    return record


def main() -> None:
    e1 = json.loads((ROOT / "artifacts/e1_baseline_results.json").read_text(encoding="utf-8"))
    e2 = json.loads((ROOT / "artifacts/e2_chunk_pool_results.json").read_text(encoding="utf-8"))
    selection = json.loads((ROOT / "config/evidence_selection.json").read_text(encoding="utf-8"))
    answer = json.loads((ROOT / "config/grounded_answer.json").read_text(encoding="utf-8"))
    citation = json.loads((ROOT / "config/citation_verification.json").read_text(encoding="utf-8"))
    answer_key = json.loads((ROOT / "answer_key/authority_answer_key.json").read_text(encoding="utf-8"))

    evaluation_entries = [entry for entry in answer_key["entries"] if entry.get("status") == "evaluation"]
    result = {
        "freeze_version": FREEZE_VERSION,
        "scope": "Week 10 configuration freeze before Week 11 evaluation; no Week 11 metrics are included.",
        "datasets_and_splits": {
            "ildc_single": {
                "splits": {split: split_record(split) for split in ("train", "validation", "test")},
                "facts_extraction": file_record("config/facts_extraction.json"),
                "known_limitation": "ILDC decision dates are year-granular; strict precedent filtering uses eCourts exact decision dates.",
            },
            "ecourts_retrieval_corpus": {
                "dataset_manifest": file_record("corpus/dataset_manifest.md"),
                "alignment_gated_crosswalk": file_record("corpus/dedup_matches.csv"),
                "cleaning_record": file_record("corpus/ecourts/cleaning_record.json"),
                "bm25_index": file_record("retrieval/bm25.sqlite"),
                "index_build_record": file_record("artifacts/bm25_index.json"),
            },
        },
        "experiments": {
            "E1": {
                "config": file_record("config/e1_baseline.json"),
                "result": file_record("artifacts/e1_baseline_results.json"),
                "random_seed": e1["config_path"] and json.loads((ROOT / "config/e1_baseline.json").read_text(encoding="utf-8"))["random_seed"],
                "test_metrics": e1["test_metrics"],
            },
            "E2_corrected": {
                "config": file_record("config/e2_chunk_pool.json"),
                "result": file_record("artifacts/e2_chunk_pool_results.json"),
                "random_seed": e2["training"]["seed"],
                "model": e2["model"],
                "test_metrics": e2["test_document_metrics"],
            },
            "E4": {
                "implementation": {
                    relative_path: file_record(relative_path)
                    for relative_path in (
                        "src/legal_xai/retrieval.py",
                        "src/legal_xai/evidence_pipeline.py",
                        "src/legal_xai/grounded_answer.py",
                        "src/legal_xai/citation_verifier.py",
                        "scripts/run_grounded_answer_pipeline.py",
                    )
                },
                "answer_renderer": answer,
                "citation_verifier": citation,
                "retrieval_selection": selection,
                "temporal_policy": "precedent_decision_year < ildc_query_year; same-year is ambiguous and excluded; missing decision date is excluded.",
                "duplicate_policy": "Exclude alignment-gated target/near-case source IDs and any direct source document meeting the six-token content self-match threshold.",
                "answer_key": {
                    "record": file_record("answer_key/authority_answer_key.json"),
                    "evaluation_entries": len(evaluation_entries),
                    "evaluation_target": 40,
                    "dev_example_entries": sum(entry.get("status") == "dev_example" for entry in answer_key["entries"]),
                },
            },
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {
                name: package_version(name)
                for name in ("scikit-learn", "pyarrow", "psycopg", "pytest", "torch", "transformers")
            },
            "database_url_source": "LEGAL_XAI_DATABASE_URL environment variable or scripts/load_provenance.py default; credentials are intentionally not frozen in the repository.",
            "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES", "not-set"),
        },
        "replay_contract": {
            "script": "scripts/run_week10_reproducibility_replay.py",
            "query": {"query_id": "week10-replay-01", "query_year": 2020, "query": "anticipatory bail section 438"},
            "comparison": "Two independent E4 runs must match after excluding generated retrieval run IDs; selected chunks, answer structure, citations, temporal counts, and provenance must be identical.",
        },
    }
    config_path = ROOT / "config/reproducibility_freeze.json"
    config_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown = "\n".join([
        "# Week 10 Reproducibility Freeze",
        "",
        "This is the pre-evaluation freeze for the fixed data, model, retrieval, explanation, and safety configuration. It does not contain Week 11 evaluation results.",
        "",
        f"- Freeze version: `{FREEZE_VERSION}`",
        f"- ILDC split rows: train `{result['datasets_and_splits']['ildc_single']['splits']['train']['rows']}`, validation `{result['datasets_and_splits']['ildc_single']['splits']['validation']['rows']}`, test `{result['datasets_and_splits']['ildc_single']['splits']['test']['rows']}`",
        f"- Retrieval configuration: `{selection['selection_version']}`; query builder `{selection['query_construction_version']}`; candidate depth `{selection['candidate_k']}`; selected sources `{selection['max_selected_evidence']}`.",
        "- Temporal policy: candidate year must be strictly earlier than query year; same-year is logged as ambiguous and excluded; missing dates are excluded.",
        "- Duplicate policy: alignment-gated target/near-case exclusion plus direct six-token source-text self-match exclusion.",
        f"- E1 seed: `{result['experiments']['E1']['random_seed']}`. E2 seed: `{result['experiments']['E2_corrected']['random_seed']}`.",
        f"- Answer key: `{len(evaluation_entries)}/40` evaluation entries, with the separate dev/example record retained outside metric computation.",
        "- The complete machine-readable freeze, including SHA-256 hashes for every frozen source, is `config/reproducibility_freeze.json`.",
        "- The bounded replay contract is executed by `scripts/run_week10_reproducibility_replay.py`.",
        "",
    ])
    (ROOT / "artifacts/week10_reproducibility_freeze.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"freeze_version": FREEZE_VERSION, "output": str(config_path)}, indent=2))


if __name__ == "__main__":
    main()
