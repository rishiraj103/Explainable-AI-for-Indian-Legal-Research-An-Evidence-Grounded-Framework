from pathlib import Path

from legal_xai.facts import (
    extract_case_facts,
    facts_input_is_eligible,
    find_outcome_cues,
    load_facts_extraction_rule,
)


RULE = load_facts_extraction_rule(Path("config/facts_extraction.json"))


def test_dispositive_cue_excludes_the_outcome_sentence() -> None:
    source = (
        "The parties entered a contract. The tribunal rejected the claim. "
        "The appeal is allowed with costs. "
        + "Later opinion text is deliberately outside the extracted input. " * 10
    )
    result = extract_case_facts(source, RULE)
    assert result.boundary_reason == "dispositive_cue"
    assert result.text == "The parties entered a contract. The tribunal rejected the claim."
    assert "appeal is allowed" not in result.text.casefold()


def test_section_header_excludes_closing_section() -> None:
    source = "The parties dispute a land transfer.\n\nORDER\n\nThe petition is dismissed."
    result = extract_case_facts(source, RULE)
    assert result.boundary_reason == "section_header"
    assert result.text == "The parties dispute a land transfer."


def test_first_of_multiple_cues_is_used() -> None:
    source = "The appellant challenged the assessment. We therefore allow the appeal. The order is set aside."
    result = extract_case_facts(source, RULE)
    assert result.text == "The appellant challenged the assessment."


def test_no_boundary_uses_the_frozen_positional_cap() -> None:
    source = "The appellant filed evidence concerning the disputed tax assessment."
    result = extract_case_facts(source, RULE)
    assert result.text.startswith("The appellant filed evidence")
    assert result.boundary_reason == "positional_cap"
    assert result.boundary_char is not None


def test_short_prefix_can_end_at_the_cue_without_outcome_leakage() -> None:
    source = "Facts. The appeal is dismissed."
    result = extract_case_facts(source, RULE)
    assert result.text == "Facts."
    assert "dismissed" not in result.text.casefold()


def test_late_dispositive_cue_is_limited_by_the_positional_cap() -> None:
    source = ("The record describes the dispute. " * 40) + "The appeal is dismissed."
    result = extract_case_facts(source, RULE)
    assert result.boundary_reason == "positional_cap"
    assert result.retained_char_count < len(source) * 0.61


def test_empty_input_is_explicit() -> None:
    result = extract_case_facts(None, RULE)
    assert result.boundary_reason == "empty_input"
    assert result.text == ""


def test_low_retention_slice_is_excluded_from_facts_only_experiments() -> None:
    source = "Background. We dismiss the appeal. " + ("Later opinion text. " * 100)
    result = extract_case_facts(source, RULE)
    assert result.boundary_reason == "dispositive_cue"
    assert not facts_input_is_eligible(result, RULE)


def test_validation_cue_scan_finds_remaining_outcome_language() -> None:
    assert find_outcome_cues("The appeal is allowed.", RULE) == ["The appeal is allowed"]
