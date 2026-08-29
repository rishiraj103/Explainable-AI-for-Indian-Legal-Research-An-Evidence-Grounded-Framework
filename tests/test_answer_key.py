from legal_xai.answer_key import is_test_split_case


def test_test_split_membership_uses_normalized_case_id() -> None:
    assert is_test_split_case(" 2019_890 ", {"2019_890"})


def test_non_test_case_is_rejected_for_evaluation() -> None:
    assert not is_test_split_case("2019_890", {"2020_1"})
