import json

from legal_xai.answer_key import is_dev_only_case, is_test_split_case, mirror_source_quality_status


def test_test_split_membership_uses_normalized_case_id() -> None:
    assert is_test_split_case(" 2019_890 ", {"2019_890"})


def test_non_test_case_is_rejected_for_evaluation() -> None:
    assert not is_test_split_case("2019_890", {"2020_1"})


def test_dev_only_gate_accepts_train_or_validation_but_never_test() -> None:
    assert is_dev_only_case("2019_890", {"2019_890"}, set(), {"2019_1"})
    assert is_dev_only_case("2018_5", set(), {"2018_5"}, {"2019_1"})
    assert not is_dev_only_case("2019_1", {"2019_1"}, set(), {"2019_1"})


def test_mirror_quality_status_marks_repaired_and_excluded_sources(tmp_path) -> None:
    record = {
        "repair_source_ids": ["repaired", "excluded"],
        "years": [{"repair_outcomes": [{"source_id": "excluded", "status": "excluded_residual_low_quality"}]}],
    }
    path = tmp_path / "cleaning_record.json"
    path.write_text(json.dumps(record), encoding="utf-8")

    assert mirror_source_quality_status("native", path) == "native-text"
    assert mirror_source_quality_status("repaired", path) == "OCR-repaired"
    assert mirror_source_quality_status("excluded", path) == "excluded_low_quality"
