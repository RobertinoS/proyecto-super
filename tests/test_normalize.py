import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from normalize import calculate_reference_price, clean_text, detect_presentation, parse_argentine_price


def test_parse_argentine_price():
    assert parse_argentine_price("$ 1.234,50") == 1234.5
    assert parse_argentine_price("4.899") == 4899.0
    assert parse_argentine_price("930.0") == 930.0


def test_clean_text_removes_accents():
    assert clean_text("Aceite Canuelas 1,5 L") == "aceite canuelas 1,5 l"


def test_detect_presentation_and_reference_price():
    data = detect_presentation("Yerba Mate 500 grs")
    assert data["normalized_qty"] == 0.5
    assert data["normalized_unit"] == "kg"
    ref, unit = calculate_reference_price(1000, "Yerba Mate 500 grs")
    assert ref == 2000
    assert unit == "kg"
