"""Check an authority-key candidate before source-verification work begins."""

from __future__ import annotations

import argparse
from pathlib import Path

from legal_xai.answer_key import is_test_split_case, load_test_split_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True, help="ILDC case ID to check")
    parser.add_argument(
        "--test-split",
        type=Path,
        default=Path("corpus/ildc/single_test.parquet"),
        help="Fixed ILDC Single test-split parquet file",
    )
    args = parser.parse_args()

    test_case_ids = load_test_split_ids(args.test_split)
    if not is_test_split_case(args.case_id, test_case_ids):
        raise SystemExit(
            f"REJECTED: {args.case_id!r} is not in the fixed ILDC test split; "
            "do not begin source verification for an evaluation entry."
        )
    print(
        f"APPROVED: {args.case_id!r} is in the fixed ILDC test split; "
        "it may enter source verification for the evaluation answer key."
    )


if __name__ == "__main__":
    main()
