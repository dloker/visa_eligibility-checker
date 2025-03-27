from data_cleanser import clean_text

def test_clean_text_removes_extra_spaces_and_non_ascii():
    raw_text = "This  is   a   test\n\n with  non-ASCII: é, ö, ü!"
    cleaned = clean_text(raw_text)
    # non-ascii characters should be removed and whitespace normalized
    assert "é" not in cleaned
    assert "  " not in cleaned
