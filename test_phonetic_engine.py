import pytest
from phonetic_engine import PhoneticEngine

@pytest.fixture
def engine():
    # Mini vocabulary for testing
    vocab = ["dom", "tom", "krowa", "sowa", "mama", "tata", "design"]
    return PhoneticEngine(vocab)

def test_normalize_basic(engine):
    assert engine.normalize("Dom") == "dom"
    assert engine.normalize("Ścieżka") == "sciezka"
    assert engine.normalize("Dziwny") == "dzwni"  # dż/dzi -> dz, y->i
    assert engine.normalize("Chleb") == "hleb"

def test_normalize_digraphs(engine):
    assert engine.normalize("design") == "dizajn"
    # business -> biznes is in the map
    assert engine.normalize("business") == "biznes" 

def test_get_vowel_positions(engine):
    # 'dom' -> 1 vowel at index 1 ('o')
    assert engine.get_vowel_positions("dom") == [1]
    # 'sowa' -> 'o' at 1, 'a' at 3
    assert engine.get_vowel_positions("sowa") == [1, 3]
    # 'niebo' -> 'i' is softener, so vowels are 'e', 'o'. 
    # n-i-e-b-o. i (index 1) checks: prev 'n' not vowel. next 'e' is vowel. Skips.
    # 'e' at 2, 'o' at 4.
    assert engine.get_vowel_positions("niebo") == [2, 4]

def test_build_entry(engine):
    entry = engine.build_entry("krowa")
    assert entry.original == "krowa"
    assert entry.normalized == "krowa"
    assert entry.vowels == 2
    # tail_d2 for 'krowa' (2 syllables) should be 'owa'
    assert entry.tail_d2 == "owa"
    # tail_d1 for 'krowa' should be 'a' (last vowel 'a' till end)
    assert entry.tail_d1 == "a"

def test_find_candidates_perfect(engine):
    # 'dom' rhymes with 'tom'
    results = engine.find_candidates("dom")
    words = [r[0] for r in results]
    assert "tom" in words
    assert "dom" not in words # Should not return itself if seen set handled in server, 
                              # but engine returns everything from index. 
                              # Ah, engine.find_candidates filters `seen = {target.original}`.
    
    # 'krowa' rhymes with 'sowa'
    results = engine.find_candidates("krowa")
    words = [r[0] for r in results]
    assert "sowa" in words
