"""Gate a retrieval-tuning probe before any source-verification work begins.

Only ILDC Single train/validation entries may be used for pre-freeze retrieval
investigation. Fixed-test entries are rejected even if an identifier appears
in more than one input file.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from legal_xai.answer_key import is_dev_only_case, load_split_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True, help="ILDC case ID to check")
    parser.add_argument("--train-split", type=Path, default=Path("corpus/ildc/single_train.parquet"))
    parser.add_argument(
        "--validation-split", type=Path, default=Path("corpus/ildc/single_validation.parquet")
    )
    parser.add_argument("--test-split", type=Path, default=Path("corpus/ildc/single_test.parquet"))
    args = parser.parse_args()

    if not is_dev_only_case(
        args.case_id,
        load_split_ids(args.train_split),
        load_split_ids(args.validation_split),
        load_split_ids(args.test_split),
    ):
        raise SystemExit(
            f"REJECTED: {args.case_id!r} is not an ILDC train/validation-only case; "
            "do not use it for retrieval tuning."
        )
    print(
        f"APPROVED: {args.case_id!r} is in ILDC train/validation and outside the fixed test split; "
        "it may enter dev-only source verification."
    )


if __name__ == "__main__":
    main()
