import re
from collections import Counter

def process():
    # Regex for Polish words: only letters (including polish ones)
    pl_word_re = re.compile(r'^[a-ząćęłńóśźż]{3,}$')
    vowels = set("aeiouyąęó")

    # 1. Load frequency words
    freq_words = []
    try:
        with open("words_freq.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    w = parts[0].lower()
                    if pl_word_re.match(w):
                        v_count = sum(1 for char in w if char in vowels)
                        # Filter out things like 'aaaa' or 'bzzzz'
                        if v_count >= 1:
                             freq_words.append(w)
    except FileNotFoundError:
        print("words_freq.txt not found")

    # 2. Load lyrics words
    lyrics_words = set()
    try:
        with open("lyrics_corrected.txt", "r", encoding="utf-8") as f:
            text = f.read().lower()
            # extract words
            words = re.findall(r'\b[a-ząćęłńóśźż]{3,}\b', text)
            lyrics_words.update(words)
    except FileNotFoundError:
        print("lyrics_corrected.txt not found")

    # 3. Combine
    # We want lyrics words to definitely be there.
    # We want common words to be there.
    # 50k frequency words + all lyrics words
    combined = set(freq_words) | lyrics_words
    
    # 4. Filter out some obvious junk if needed (non-polish letters were already handled in findall)
    # But freq_words might have some foreign words.
    
    # 5. Sort
    sorted_words = sorted(list(combined))
    
    with open("words_pl.txt", "w", encoding="utf-8") as f:
        for w in sorted_words:
            f.write(w + "\n")

    # 6. Create scores mapping
    # 0.5 base, 1.0 if high freq, 2.0 if in lyrics
    scores = {}
    lyrics_set = set(lyrics_words)
    freq_set = set(freq_words[:15000]) # top 15k are "high freq"
    
    for w in sorted_words:
        score = 0.5
        if w in freq_set: score += 0.5
        if w in lyrics_set: score += 1.0
        scores[w] = score

    import json
    with open("word_scores.json", "w", encoding="utf-8") as f:
        json.dump(scores, f)
            
    print(f"Vocab updated: {len(sorted_words)} words. Scores saved.")

if __name__ == "__main__":
    process()
