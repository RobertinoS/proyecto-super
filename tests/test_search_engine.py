import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from search_engine import similarity


def test_similarity_exactish_match():
    assert similarity("yerba playadito", "Yerba Mate Playadito Suave 1 Kg") > 80


def test_similarity_low_match():
    assert similarity("detergente", "Aceite Girasol 1.5 L") < 60
