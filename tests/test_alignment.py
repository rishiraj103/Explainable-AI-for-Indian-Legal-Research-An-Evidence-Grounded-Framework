from legal_xai.alignment import assess_content_alignment, shared_six_token_phrases


def test_alignment_requires_metadata_and_direct_document_content() -> None:
    source = "Alice Example versus Bob Example disputed a tenancy agreement for a shop. " * 120
    result = assess_content_alignment(
        ildc_text=source,
        source_text=source,
        title="Alice Example versus Bob Example",
        petitioner="Alice Example",
        respondent="Bob Example",
    )
    assert result.title_party_passed
    assert result.direct_content_passed
    assert result.passed


def test_syntactic_candidate_is_rejected_when_document_content_differs() -> None:
    result = assess_content_alignment(
        ildc_text="Ravi Kumar challenged a dismissal from public service. " * 120,
        source_text="Mira Club challenged income tax on bank interest. " * 120,
        title="Mira Club versus Commissioner of Income Tax",
        petitioner="Mira Club",
        respondent="Commissioner of Income Tax",
    )
    assert not result.title_party_passed
    assert not result.direct_content_passed
    assert not result.passed


def test_direct_phrase_counter_can_stop_at_gate_threshold() -> None:
    text = "one two three four five six seven eight nine ten " * 30
    count, example = shared_six_token_phrases(text, text, stop_at=10)
    assert count == 10
    assert example == "one two three four five six"
