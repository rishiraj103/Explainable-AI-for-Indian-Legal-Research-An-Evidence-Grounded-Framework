from legal_xai.corpus import (
    chunk_page_text,
    clean_page_text,
    is_non_evidentiary_chunk,
    repeated_page_furniture,
)


def test_clean_page_text_removes_known_extraction_clutter() -> None:
    raw = "A\n1043\nThe regula-\ntion applies.\n\nB\n1043\n"
    assert clean_page_text(raw) == "The regulation applies."


def test_clean_page_text_preserves_meaningful_number_in_sentence() -> None:
    assert clean_page_text("Section 3 applies.\n45\n") == "Section 3 applies."


def test_repeated_page_furniture_is_removed_only_when_repeated_within_document() -> None:
    pages = [
        "A\nREPORT HEADER\nThe first page.\nCASE TITLE\n1",
        "B\nREPORT HEADER\nThe second page.\nCASE TITLE\n2",
        "C\nREPORT HEADER\nThe third page.\nCASE TITLE\n3",
    ]
    furniture = repeated_page_furniture(pages)
    assert "report header" in furniture
    assert "case title" in furniture
    assert clean_page_text(pages[0], furniture) == "The first page."


def test_non_evidentiary_filter_excludes_lists_and_fragments_but_keeps_short_order() -> None:
    assert is_non_evidentiary_chunk("A. Rao, B. Singh, C. Ali, D. Khan, Advs.")
    assert is_non_evidentiary_chunk("There are")
    assert not is_non_evidentiary_chunk("Appeal dismissed.")


def test_chunks_are_sentence_aligned_and_locatable() -> None:
    text = "One is short. Two is short. Three is short."
    chunks = chunk_page_text(text, 7, max_words=20, max_sentences=2)
    assert [chunk.text for chunk in chunks] == ["One is short. Two is short.", "Three is short."]
    assert [chunk.chunk_number for chunk in chunks] == [1, 2]
    assert all(chunk.page_number == 7 for chunk in chunks)
    assert text[chunks[0].start_char:chunks[0].end_char] == chunks[0].text


def test_long_sentence_is_not_silently_truncated() -> None:
    text = "This single sentence has more than five words and must stay intact."
    assert chunk_page_text(text, 1, max_words=5, max_sentences=1)[0].text == text
