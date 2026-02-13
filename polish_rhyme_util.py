"""
Polish rhyme utility module.
Provides syllable counting, phonetic suffix extraction, rhyme scheme verification,
and a RhymeFinder class backed by PhoneticEngine.
"""

import re
from phonetic_engine import PhoneticEngine

# Shared engine instance (lazy-loaded with vocabulary)
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        try:
            with open("words_pl.txt", "r", encoding="utf-8") as f:
                vocab = [line.strip().lower() for line in f if len(line.strip()) > 2]
        except FileNotFoundError:
            vocab = []
        _engine = PhoneticEngine(vocab)
    return _engine


# --- Polish vowels for syllable counting ---
_PL_VOWELS = set('aeęąioóuy')

def count_syllables(word: str) -> int:
    """Count syllables in a Polish word (= number of vowel groups)."""
    word = re.sub(r'[^\w]', '', word.lower())
    count = 0
    in_vowel = False
    for ch in word:
        if ch in _PL_VOWELS:
            if not in_vowel:
                count += 1
                in_vowel = True
        else:
            in_vowel = False
    return max(count, 1) if word else 0


def get_phonetic_suffix(word: str, depth: int = 2) -> str:
    """
    Return the phonetic suffix of a word (last `depth` vowel nuclei + trailing consonants).
    Uses PhoneticEngine.normalize for consistent representation.
    """
    engine = _get_engine()
    clean = re.sub(r'[^\w]', '', word.lower())
    norm = engine.normalize(clean)
    vowel_positions = engine.get_vowel_positions(norm)

    if not vowel_positions:
        return norm

    start = vowel_positions[-min(depth, len(vowel_positions))]
    return norm[start:]


def verify_rhyme_scheme(stanza: list[str], scheme: str = "AABB") -> tuple[bool, list[str]]:
    """
    Verify that a stanza follows the given rhyme scheme.
    Returns (is_match, list_of_suffixes).

    Supported schemes: AABB, ABAB, ABBA
    """
    suffixes = []
    for line in stanza:
        words = line.strip().split()
        if not words:
            suffixes.append("")
            continue
        last_word = re.sub(r'[^\w]', '', words[-1])
        suffixes.append(get_phonetic_suffix(last_word))

    if len(suffixes) < 4:
        return False, suffixes

    def rhymes(a: str, b: str) -> bool:
        """Two suffixes rhyme if they share at least the last vowel+tail."""
        sa = get_phonetic_suffix_raw(a)
        sb = get_phonetic_suffix_raw(b)
        return sa == sb or a == b

    # For comparing suffixes directly (already extracted), just compare tail_d1
    def tail1(s: str) -> str:
        engine = _get_engine()
        vp = engine.get_vowel_positions(s)
        if not vp:
            return s
        return s[vp[-1]:]

    t = [tail1(s) for s in suffixes]

    if scheme == "AABB":
        ok = (t[0] == t[1]) and (t[2] == t[3])
    elif scheme == "ABAB":
        ok = (t[0] == t[2]) and (t[1] == t[3])
    elif scheme == "ABBA":
        ok = (t[0] == t[3]) and (t[1] == t[2])
    else:
        ok = False

    return ok, suffixes


def get_phonetic_suffix_raw(word: str) -> str:
    """Simplified: return tail_d1 of a normalized word (last vowel + rest)."""
    engine = _get_engine()
    norm = engine.normalize(re.sub(r'[^\w]', '', word.lower()))
    vp = engine.get_vowel_positions(norm)
    if not vp:
        return norm
    return norm[vp[-1]:]


class RhymeFinder:
    """Wrapper around PhoneticEngine for finding rhymes from the vocabulary."""

    def __init__(self, vocabulary_path: str = "words_pl.txt"):
        try:
            with open(vocabulary_path, "r", encoding="utf-8") as f:
                vocab = [line.strip().lower() for line in f if len(line.strip()) > 2]
        except FileNotFoundError:
            vocab = []
        self.engine = PhoneticEngine(vocab)

    def find_rhymes(self, word: str, limit: int = 10) -> list[str]:
        """Find rhyming words for the given word."""
        results = self.engine.find_candidates(word)
        return [w for w, grade, score in results[:limit]]
