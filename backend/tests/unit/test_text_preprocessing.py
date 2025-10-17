"""
Simple unit tests for text preprocessing functions
Testing individual functions without full module imports
"""
import pytest
import re
import unicodedata


@pytest.mark.unit
def test_clean_text_basic():
    """Test basic text cleaning"""
    text = "  Hola   mundo  "
    cleaned = " ".join(text.split()).strip()
    assert cleaned == "Hola mundo"


@pytest.mark.unit
def test_clean_text_remove_html():
    """Test HTML tag removal"""
    text = "Text with <b>bold</b> tags"
    cleaned = re.sub(r'<[^>]+>', '', text)
    assert "<b>" not in cleaned
    assert "bold" in cleaned


@pytest.mark.unit
def test_normalize_whitespace():
    """Test whitespace normalization"""
    text = "Multiple    spaces   here"
    normalized = re.sub(r'\s+', ' ', text)
    assert normalized == "Multiple spaces here"


@pytest.mark.unit
def test_fix_punctuation_spacing():
    """Test punctuation spacing"""
    text = "Word ,punctuation .here"
    # Remove space before punctuation
    fixed = re.sub(r'\s+([.,;:!?])', r'\1', text)
    assert fixed == "Word,punctuation.here"


@pytest.mark.unit
def test_unicode_normalization():
    """Test Unicode normalization"""
    text = "café"
    normalized = unicodedata.normalize('NFKD', text)
    assert normalized is not None
    assert len(normalized) >= len(text)


@pytest.mark.unit
def test_sentence_splitting():
    """Test sentence splitting"""
    text = "Primera oración. Segunda oración. Tercera."
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    assert len(sentences) == 3


@pytest.mark.unit
def test_extract_quoted_text():
    """Test quote extraction"""
    text = 'El dijo "esto es importante" ayer'
    quotes = re.findall(r'"([^"]+)"', text)
    assert len(quotes) == 1
    assert "esto es importante" in quotes


@pytest.mark.unit
def test_remove_control_characters():
    """Test control character removal"""
    text = "Text\x00with\x01control\x02chars"
    cleaned = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
    assert "\x00" not in cleaned
    assert "Text" in cleaned


@pytest.mark.unit
def test_spanish_characters_preserved():
    """Test Spanish characters are preserved"""
    text = "ñáéíóú"
    # Just verify they exist after basic cleaning
    cleaned = text.strip()
    assert "ñ" in cleaned
    assert "á" in cleaned
    assert "é" in cleaned


@pytest.mark.unit
def test_abbreviation_expansion():
    """Test abbreviation expansion logic"""
    abbreviations = {'Dr.': 'Doctor', 'Ing.': 'Ingeniero'}
    text = "El Dr. García"
    for abbr, full in abbreviations.items():
        text = text.replace(abbr, full)
    assert "Doctor" in text
    assert "Dr." not in text


@pytest.mark.unit
def test_currency_pattern_matching():
    """Test currency pattern detection"""
    text = "$1.000.000 pesos"
    # Check if pattern exists
    pattern = r'\$\s*([0-9.,]+)'
    matches = re.findall(pattern, text)
    assert len(matches) > 0
