"""Download the Week 2 dual-corpus foundation without downloading judgment PDFs."""

from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi, hf_hub_download


ILDC_REPOSITORY = "Exploration-Lab/IL-TUR"
ILDC_FILES = {
    "train": "cjpe/single_train-00000-of-00001.parquet",
    "dev_pool": "cjpe/single_dev-00000-of-00001.parquet",
    "test": "cjpe/test-00000-of-00001.parquet",
}
ECOURTS_URL = "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/parquet/year={year}/metadata.parquet"


def download_ecourts_metadata(year: int, destination: Path) -> tuple[bool, int | None]:
    """Download one public, unsigned S3 metadata Parquet object if it exists."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return True, destination.stat().st_size

    request = urllib.request.Request(ECOURTS_URL.format(year=year), method="GET")
    temporary = destination.with_suffix(".parquet.part")
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            temporary.unlink(missing_ok=True)
            return False, None
        temporary.unlink(missing_ok=True)
        raise
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    temporary.replace(destination)
    return True, destination.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2020)
    args = parser.parse_args()

    corpus_root: Path = args.corpus_root
    ildc_root = corpus_root / "ildc"
    ecourts_root = corpus_root / "ecourts" / "metadata"
    ildc_root.mkdir(parents=True, exist_ok=True)

    api = HfApi()
    dataset_info = api.dataset_info(ILDC_REPOSITORY)
    ildc_record = {"repository": ILDC_REPOSITORY, "revision": dataset_info.sha, "files": {}}
    for split, remote_file in ILDC_FILES.items():
        cached_file = Path(
            hf_hub_download(
                repo_id=ILDC_REPOSITORY,
                repo_type="dataset",
                filename=remote_file,
                revision=dataset_info.sha,
            )
        )
        local_file = ildc_root / f"single_{split}.parquet"
        if not local_file.exists() or local_file.stat().st_size != cached_file.stat().st_size:
            shutil.copy2(cached_file, local_file)
        ildc_record["files"][split] = {
            "remote_path": remote_file,
            "local_path": local_file.as_posix(),
            "bytes": local_file.stat().st_size,
        }

    # The IL-TUR distribution supplies the original validation-plus-test pool
    # and a separate test split. Removing the test IDs recovers the 994-row
    # ILDC Single validation split without altering its records.
    dev_pool = pd.read_parquet(ildc_root / "single_dev_pool.parquet")
    test = pd.read_parquet(ildc_root / "single_test.parquet")
    validation = dev_pool.loc[~dev_pool["id"].isin(set(test["id"]))].copy()
    validation_file = ildc_root / "single_validation.parquet"
    validation.to_parquet(validation_file, index=False)
    ildc_record["files"]["validation"] = {
        "derived_from": "single_dev_pool minus IDs in single_test",
        "local_path": validation_file.as_posix(),
        "rows": len(validation),
        "bytes": validation_file.stat().st_size,
    }

    ecourts_record = {"available_years": [], "unavailable_years": [], "files": {}}
    for year in range(args.start_year, args.end_year + 1):
        destination = ecourts_root / f"year={year}" / "metadata.parquet"
        available, size = download_ecourts_metadata(year, destination)
        if available:
            ecourts_record["available_years"].append(year)
            ecourts_record["files"][str(year)] = {"path": destination.as_posix(), "bytes": size}
        else:
            ecourts_record["unavailable_years"].append(year)

    record = {
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
        "scope": {"requested_years": [args.start_year, args.end_year], "pdfs_downloaded": False},
        "ildc": ildc_record,
        "ecourts": ecourts_record,
    }
    (corpus_root / "download_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
