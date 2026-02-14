import re
import os
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
    
    # 3. Load Vulgar words
    vulgar_words = set()
    try:
        with open(os.path.join("data", "vulgar.txt"), "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w: vulgar_words.add(w)
    except FileNotFoundError:
        print("data/vulgar.txt not found")

    # 4. Load Entities
    # Format: Name|Inflection1,Inflection2|tag
    entity_map = {} # word -> {"tag": tag, "base": base_name}
    try:
        with open(os.path.join("data", "entities.txt"), "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    base_name = parts[0]
                    inflections = parts[1].split(",")
                    tag = parts[2]
                    
                    # Add base name parts if single word
                    if " " not in base_name:
                         w = base_name.lower()
                         entity_map[w] = {"tag": tag, "base": base_name}
                    
                    # Add inflections
                    for infl in inflections:
                        w = infl.strip().lower()
                        if w:
                            entity_map[w] = {"tag": tag, "base": base_name}
    except FileNotFoundError:
        print("data/entities.txt not found")

    # 5. Combine everything
    # 50k freq + lyrics + vulgar + entities
    combined = set(freq_words) | lyrics_words | vulgar_words | set(entity_map.keys())
    
    # 6. Sort
    sorted_words = sorted(list(combined))
    
    with open("words_pl.txt", "w", encoding="utf-8") as f:
        for w in sorted_words:
            f.write(w + "\n")

    # 7. Create scores & metadata mapping
    # Schema: "word": {"score": float, "flags": [str]}
    metadata = {}
    lyrics_set = set(lyrics_words)
    freq_set = set(freq_words[:15000]) # top 15k are "high freq"
    
    for w in sorted_words:
        score = 0.5
        flags = []
        
        # Base scoring
        if w in freq_set: score += 0.5
        if w in lyrics_set: score += 1.0
        
        # Entity logic
        if w in entity_map:
            ent = entity_map[w]
            score += 2.0 # Huge boost for matching an entity
            flags.append("entity")
            flags.append(ent["tag"]) # e.g. "rapper", "city"
            
        # Vulgar logic
        if w in vulgar_words:
            # Maybe slight boost to ensure they appear if requested, but not too high
            # Actually user said "highlight", not "hide".
            # Let's give them good visibility.
            if score < 1.0: score = 1.0
            flags.append("vulgar")

        # Save compact if interesting, else just score
        # For backward compatibility or size, we can just save the dict object
        match_data = {"s": round(score, 2)}
        if flags:
            match_data["f"] = flags
        
        metadata[w] = match_data

    import json
    with open("word_scores.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f)
            
    print(f"Vocab updated: {len(sorted_words)} words. Metadata saved.")

if __name__ == "__main__":
    process()
