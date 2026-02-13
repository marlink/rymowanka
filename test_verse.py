import re
from polish_rhyme_util import count_syllables, get_phonetic_suffix

def verify_stanza(lines, target_syllables=11):
    print(f"{'Line':<40} | {'Syllables':<10} | {'Rhyme Suffix'}")
    print("-" * 70)
    for line in lines:
        words = line.split()
        last_word = re.sub(r'[^\w\s]', '', words[-1])
        s_count = sum(count_syllables(w) for w in words)
        rhyme = get_phonetic_suffix(last_word)
        print(f"{line:<40} | {s_count:<10} | {rhyme}")

# Example: 11-syllable Sapphic style (5+6) with AABB rhymes
verse = [
    "Srebrzysty księżyc płynie po niebie", # 11
    "Szukam w tej ciszy dzisiaj sam siebie", # 11
    "Wiatr cicho śpiewa starą piosenkę",   # 11
    "Prowadzi serce moje za rękę"          # 11
]

verify_stanza(verse)
