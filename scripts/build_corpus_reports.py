"""Create the dataset manifest and ILDC/eCourts leakage report from local metadata."""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from legal_xai.temporal import assess_temporal_eligibility


ECOURTS_COLUMNS = [
    "title",
    "petitioner",
    "respondent",
    "citation",
    "case_id",
    "decision_date",
    "disposal_nature",
    "court",
    "path",
    "year",
]
STOP_WORDS = {
    "and", "the", "of", "for", "with", "ors", "anr", "another", "others", "state", "india",
    "union", "ltd", "limited", "court", "supreme", "commission", "department", "authority",
}


def normalized_tokens(value: object) -> set[str]:
    text = "" if value is None else str(value).lower()
    return {token for token in re.findall(r"[a-z][a-z0-9]{2,}", text) if token not in STOP_WORDS}


def ildc_id_from_ecourts_case_id(case_id: object) -> str | None:
    match = re.fullmatch(r"\s*(\d{4})\s+INSC\s+(\d+)\s*", "" if case_id is None else str(case_id))
    return f"{match.group(1)}_{int(match.group(2))}" if match else None


def load_ildc(corpus_root: Path) -> pd.DataFrame:
    split_paths = {
        "train": corpus_root / "ildc" / "single_train.parquet",
        "validation": corpus_root / "ildc" / "single_validation.parquet",
        "test": corpus_root / "ildc" / "single_test.parquet",
    }
    frames = []
    for split, path in split_paths.items():
        frame = pd.read_parquet(path, columns=["id", "text", "label"])
        frame["split"] = split
        frames.append(frame)
    ildc = pd.concat(frames, ignore_index=True)
    ildc["query_year"] = ildc["id"].str.extract(r"^(\d{4})_")[0].astype("Int64")
    return ildc


def load_ecourts(corpus_root: Path) -> pd.DataFrame:
    files = sorted((corpus_root / "ecourts" / "metadata").glob("year=*/metadata.parquet"))
    if not files:
        raise FileNotFoundError("No eCourts metadata files found. Run download_dual_corpus.py first.")
    return pd.concat([pd.read_parquet(path, columns=ECOURTS_COLUMNS) for path in files], ignore_index=True)


def find_near_matches(ildc: pd.DataFrame, ecourts: pd.DataFrame, exact_ildc_ids: set[str]) -> list[dict[str, object]]:
    """Find high-confidence title/party matches where the canonical IDs do not align.

    Candidates are blocked by year and distinctive title/party terms. A match
    requires at least two matching terms and at least 80% coverage of the
    eCourts title/party token set in ILDC text; this deliberately favors
    precision over recall for a leakage audit.
    """

    ecourts = ecourts.copy()
    ecourts["query_year"] = pd.to_numeric(ecourts["year"], errors="coerce").astype("Int64")
    ecourts["identity_tokens"] = ecourts.apply(
        lambda row: normalized_tokens(
            " ".join(
                "" if pd.isna(row[field]) else str(row[field])
                for field in ["title", "petitioner", "respondent"]
            )
        ),
        axis=1,
    )
    term_counts = Counter(token for tokens in ecourts["identity_tokens"] for token in tokens)
    index: dict[tuple[int, str], set[int]] = defaultdict(set)
    for ecourts_index, row in ecourts.iterrows():
        if pd.isna(row["query_year"]):
            continue
        for token in row["identity_tokens"]:
            if term_counts[token] <= 50:
                index[(int(row["query_year"]), token)].add(ecourts_index)

    matches: list[dict[str, object]] = []
    for _, ildc_row in ildc.iterrows():
        if ildc_row["id"] in exact_ildc_ids or pd.isna(ildc_row["query_year"]):
            continue
        text_tokens = normalized_tokens(ildc_row["text"])
        candidate_indexes: set[int] = set()
        for token in text_tokens:
            candidate_indexes.update(index.get((int(ildc_row["query_year"]), token), set()))
        for ecourts_index in candidate_indexes:
            candidate = ecourts.loc[ecourts_index]
            identity_tokens = candidate["identity_tokens"]
            shared = text_tokens & identity_tokens
            coverage = len(shared) / len(identity_tokens) if identity_tokens else 0.0
            if len(shared) >= 2 and coverage >= 0.8:
                matches.append(
                    {
                        "match_type": "near_title_party",
                        "score": round(coverage, 3),
                        "ildc_id": ildc_row["id"],
                        "split": ildc_row["split"],
                        "ecourts_case_id": candidate["case_id"],
                        "citation": candidate["citation"],
                        "decision_date": candidate["decision_date"],
                        "title": candidate["title"],
                    }
                )
    return matches


def write_dedup_report(corpus_root: Path, ildc: pd.DataFrame, ecourts: pd.DataFrame) -> dict[str, int]:
    raw_ecourts_rows = len(ecourts)
    ecourts = ecourts.drop_duplicates(subset=["case_id"], keep="first").copy()
    ecourts["ildc_id_candidate"] = ecourts["case_id"].map(ildc_id_from_ecourts_case_id)
    ildc_identifiers = set(ildc["id"])
    exact = ecourts.loc[ecourts["ildc_id_candidate"].isin(ildc_identifiers)].copy()
    exact_matches = ildc[["id", "split"]].merge(
        exact,
        left_on="id",
        right_on="ildc_id_candidate",
        how="inner",
    )
    exact_rows = [
        {
            "match_type": "exact_canonical_id",
            "score": 1.0,
            "ildc_id": row.id,
            "split": row.split,
            "ecourts_case_id": row.case_id,
            "citation": row.citation,
            "decision_date": row.decision_date,
            "title": row.title,
        }
        for row in exact_matches.itertuples(index=False)
    ]
    near_rows = find_near_matches(ildc, ecourts, set(exact_matches["id"]))
    all_matches = exact_rows + near_rows
    matches_file = corpus_root / "dedup_matches.csv"
    matches = pd.DataFrame(all_matches).drop_duplicates(subset=["match_type", "ildc_id", "ecourts_case_id"])
    matches.to_csv(matches_file, index=False)
    exact_case_count = len(exact_matches["id"].unique())
    near_case_count = len({row["ildc_id"] for row in near_rows})
    flagged_ildc_case_count = matches["ildc_id"].nunique()

    lines = [
        "# ILDC / eCourts Deduplication and Leakage Report",
        "",
        "## Method",
        "",
        "- Exact match: canonicalized eCourts `case_id` values of the form `YYYY INSC N` were compared with ILDC IDs of the form `YYYY_N`.",
        "- Near match: for records without an exact ID match, eCourts title/petitioner/respondent tokens were compared only with ILDC text from the same year. A near match requires at least two shared distinctive terms and 80% title/party-token coverage. This is a conservative audit and does not claim to identify every duplicate.",
        "",
        "## Results",
        "",
        f"- ILDC cases inspected: {len(ildc):,}",
        f"- eCourts metadata rows downloaded: {raw_ecourts_rows:,}",
        f"- Distinct eCourts case IDs inspected: {len(ecourts):,}",
        f"- Exact canonical-ID overlaps (unique ILDC cases): {exact_case_count:,}",
        f"- High-confidence near title/party overlaps (unique ILDC cases): {near_case_count:,}",
        f"- Unique ILDC cases flagged for exclusion review: {flagged_ildc_case_count:,}",
        f"- Unique ILDC/eCourts candidate pairs flagged: {len(matches):,}",
        "",
        "Flagged cases are recorded in `dedup_matches.csv` (local-only corpus output). Any flagged record must be excluded from that query case's retrieval candidates in E3/E4.",
    ]
    (corpus_root / "dedup_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "exact_cases": exact_case_count,
        "near_cases": near_case_count,
        "flagged_ildc_cases": flagged_ildc_case_count,
        "candidate_pairs": len(matches),
    }


def write_manifest(corpus_root: Path, ildc: pd.DataFrame, ecourts: pd.DataFrame, overlap_counts: dict[str, int]) -> None:
    ildc_counts = ildc.groupby("split").size().to_dict()
    ildc_years = ildc["query_year"].dropna().astype(int)
    ecourts_dates = pd.to_datetime(ecourts["decision_date"], format="%d-%m-%Y", errors="coerce")
    manifest = f"""# Dataset Manifest

## ILDC Single — E1/E2 prediction baseline

- **Source:** [Exploration-Lab/IL-TUR](https://huggingface.co/datasets/Exploration-Lab/IL-TUR), CJPE `single_*` Parquet files.
- **License:** CC-BY-NC, as stated by the original CJPE repository; attribution is required and commercial use is prohibited.
- **Subset loaded:** ILDC Single, {len(ildc):,} cases: {ildc_counts['train']:,} train, {ildc_counts['validation']:,} validation, and {ildc_counts['test']:,} test. The local validation split is the provided 2,511-row development pool with the 1,517 test IDs removed, yielding the original 994 validation cases.
- **Observed year range:** {ildc_years.min()}–{ildc_years.max()}, derived from the `id` prefix only.
- **Fields used:** `id`, `text`, `label`, and the fixed local split assignment. Labels are binary: rejected (0) or accepted (1).
- **Known limitations:** ILDC has no exact decision date, citation, authority metadata, or document-level provenance fields. Its year-only ID is insufficient to order same-year precedents; all same-year eCourts precedents are therefore ambiguous and excluded by default.

## Indian Supreme Court Judgments — E3/E4 evidence corpus

- **Source:** [vanga/indian-supreme-court-judgments](https://github.com/vanga/indian-supreme-court-judgments), public AWS Open Data bucket `s3://indian-supreme-court-judgments/` accessed without authentication.
- **License:** CC-BY-4.0.
- **Subset loaded:** metadata only (no PDFs), {len(ecourts):,} downloaded rows ({ecourts['case_id'].nunique():,} distinct case IDs) from yearly Parquet files for 1950–2020. The requested 1947–1949 period is unavailable because the source begins in 1950.
- **Exact-date coverage:** {ecourts_dates.notna().sum():,} records with a parseable `decision_date` out of {len(ecourts):,}; observed dates span {ecourts_dates.min().date()} to {ecourts_dates.max().date()}.
- **Fields retained for the next stage:** `title`, `petitioner`, `respondent`, `citation`, `case_id`, `decision_date`, `disposal_nature`, `court`, `path`, and `year`. The downloaded source Parquet files remain local-only.
- **Known limitations:** this stage intentionally does not download judgment PDFs or build a retrieval index. Metadata alone cannot provide the evidence passages needed for E3/E4; PDFs or authoritative text will be acquired only in the approved next-week corpus-engineering work.

## Leakage-audit summary

- **Exact canonical-ID overlaps (unique ILDC cases):** {overlap_counts['exact_cases']:,}
- **High-confidence near title/party overlaps (unique ILDC cases):** {overlap_counts['near_cases']:,}
- **Unique ILDC cases flagged for exclusion review:** {overlap_counts['flagged_ildc_cases']:,}
- **Unique ILDC/eCourts candidate pairs flagged:** {overlap_counts['candidate_pairs']:,}

The accompanying `dedup_report.md` records the matching method and the live overlap count. Flagged records must be excluded from retrieval candidates for the matching ILDC query case.
"""
    (corpus_root / "dataset_manifest.md").write_text(manifest, encoding="utf-8")


def write_temporal_overlap_audit(corpus_root: Path, ecourts: pd.DataFrame) -> None:
    """Log temporal buckets for the known ILDC/eCourts overlap candidates."""

    matches = pd.read_csv(corpus_root / "dedup_matches.csv")
    ecourts_dates = ecourts[["case_id", "decision_date"]].drop_duplicates(subset=["case_id"])
    matches = matches.merge(ecourts_dates, left_on="ecourts_case_id", right_on="case_id", how="left", suffixes=("", "_metadata"))
    decisions = matches.apply(
        lambda row: assess_temporal_eligibility(str(row["ildc_id"])[:4], row["decision_date_metadata"]),
        axis=1,
    )
    matches["temporal_status"] = [decision.status.value for decision in decisions]
    matches["temporal_reason"] = [decision.reason for decision in decisions]
    ambiguous = matches.loc[matches["temporal_status"] == "ambiguous_excluded"].copy()
    ambiguous.to_csv(corpus_root / "temporal_ambiguities.csv", index=False)
    counts = matches["temporal_status"].value_counts().to_dict()
    audit = f"""# Temporal Overlap Audit

This audit applies the reusable year-only ILDC temporal rule to the known ILDC/eCourts overlap candidates. It does not create a retrieval index.

- Candidate pairs assessed: {len(matches):,}
- Eligible (strictly earlier year): {counts.get('eligible', 0):,}
- Ambiguous — excluded by default (same year): {counts.get('ambiguous_excluded', 0):,}
- Ineligible (later year): {counts.get('ineligible', 0):,}
- Excluded for unresolved metadata: {counts.get('excluded_missing_metadata', 0):,}

The same-year bucket is stored separately in `temporal_ambiguities.csv` for later inspection. These pairs are also leakage candidates and must not be retrieved for their matching ILDC case.
"""
    (corpus_root / "temporal_overlap_audit.md").write_text(audit, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    args = parser.parse_args()

    ildc = load_ildc(args.corpus_root)
    ecourts = load_ecourts(args.corpus_root)
    overlap_counts = write_dedup_report(args.corpus_root, ildc, ecourts)
    write_temporal_overlap_audit(args.corpus_root, ecourts)
    write_manifest(args.corpus_root, ildc, ecourts, overlap_counts)


if __name__ == "__main__":
    main()
