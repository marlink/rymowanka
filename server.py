from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import re
import random
from collections import defaultdict
from fastapi.middleware.cors import CORSMiddleware
from phonetic_engine import PhoneticEngine

app = FastAPI(title="Rhyme Architect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def load_vocabulary():
    try:
        with open("words_pl.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if len(line.strip()) > 2]
    except FileNotFoundError:
        return []


def clean_last_word(text: str) -> str:
    """Extract and normalize last word: lowercase, strip all non-alpha."""
    words = text.strip().split()
    if not words:
        return ""
    return re.sub(r'[^\w]', '', words[-1].lower())


def load_lyrics_corpus(engine: PhoneticEngine):
    """Index corpus lines by their last word's phonetic tail_d2."""
    lines_by_d2 = defaultdict(list)   # tail_d2 -> [line, ...]
    lines_by_word = defaultdict(list)  # clean_last_word -> [line, ...]
    all_lines = []

    try:
        with open("lyrics_corrected.txt", "r", encoding="utf-8") as f:
            raw = f.readlines()
    except FileNotFoundError:
        return lines_by_d2, lines_by_word, all_lines

    skip = re.compile(r'^\s*$|^\[|^#|^-{3,}|^\(|^Style:|^End|^Fade|^Finish')

    for raw_line in raw:
        line = raw_line.strip()
        if not line or skip.match(line):
            continue
        line_clean = re.sub(r'\[.*?\]', '', line).strip()
        if not line_clean or len(line_clean) < 10:
            continue

        last = clean_last_word(line_clean)
        if len(last) < 2:
            continue

        entry = engine.build_entry(last)
        lines_by_d2[entry.tail_d2].append(line_clean)
        lines_by_word[last].append(line_clean)
        all_lines.append(line_clean)

    return lines_by_d2, lines_by_word, all_lines


# --- Initialize ---
VOCABULARY = load_vocabulary()
engine = PhoneticEngine(VOCABULARY)
LINES_BY_D2, LINES_BY_WORD, ALL_LINES = load_lyrics_corpus(engine)
print(f"📚 Corpus: {len(ALL_LINES)} lines, {len(LINES_BY_D2)} unique d2 tails")


# --- Models ---
class GenerationRequest(BaseModel):
    verse: str
    seen: Optional[List[str]] = []

class WordSuggestion(BaseModel):
    word: str
    grade: str
    score: float

class VerseSuggestion(BaseModel):
    line: str
    rhyme_word: str
    score: float

class GenerationResponse(BaseModel):
    mode: str
    original_word: str
    rhyme_tail: str  # expose for debugging
    words: Optional[Dict[str, List[WordSuggestion]]] = None
    verses: Optional[Dict[str, VerseSuggestion]] = None


def find_rhyming_verse(target_word: str, target_entry, seen_set: set, input_lower: str):
    """
    Find ONE corpus line that genuinely rhymes (tail_d2 match).
    No fallback to random. Returns None if no match.
    """
    # --- Strategy 1: Direct d2 corpus lookup ---
    d2_candidates = list(LINES_BY_D2.get(target_entry.tail_d2, []))
    random.shuffle(d2_candidates)

    for line in d2_candidates:
        if line.lower().strip() == input_lower:
            continue
        if line in seen_set:
            continue
        rw = clean_last_word(line)
        if rw == target_word:
            continue  # don't suggest same ending word
        return VerseSuggestion(line=line, rhyme_word=rw, score=1.0)

    # --- Strategy 2: Use word dictionary to find rhyming words,
    #     then find corpus lines ending with those words ---
    rhyming_words = engine.find_candidates(target_word)
    perfect_words = [w for w, grade, score in rhyming_words if grade == "PERFECT"]
    random.shuffle(perfect_words)

    for rw in perfect_words:
        corpus_lines = LINES_BY_WORD.get(rw, [])
        for line in corpus_lines:
            if line.lower().strip() == input_lower:
                continue
            if line in seen_set:
                continue
            return VerseSuggestion(line=line, rhyme_word=rw, score=0.9)

    # --- NO FALLBACK. No match = no suggestion. Never random. ---
    return None


@app.post("/generate", response_model=GenerationResponse)
async def generate_rhymes(request: GenerationRequest):
    text = request.verse.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty input")

    seen_set = set(request.seen or [])
    target_word = clean_last_word(text)
    if not target_word:
        raise HTTPException(status_code=400, detail="No valid word found")

    target_entry = engine.build_entry(target_word)
    is_single_word = len(text.split()) == 1

    # === DIAGNOSTIC LOG ===
    d2_count = len(LINES_BY_D2.get(target_entry.tail_d2, []))
    print(f"🔍 Input: '{text}'")
    print(f"   Target word: '{target_word}'")
    print(f"   Normalized: '{target_entry.normalized}'")
    print(f"   Rhyme tail (d2): '{target_entry.tail_d2}' | (d1): '{target_entry.tail_d1}'")
    print(f"   Matching corpus lines (d2): {d2_count}")
    print(f"   Mode: {'word' if is_single_word else 'verse'}")

    if is_single_word:
        # --- WORD MODE ---
        raw_results = engine.find_candidates(target_word)
        payload = {"PERFECT": [], "DOMINANT": [], "NEAR": []}
        for word, grade, score in raw_results:
            if len(payload[grade]) < 10:
                payload[grade].append(WordSuggestion(word=word, grade=grade, score=score))
        return GenerationResponse(
            mode="word", original_word=target_word,
            rhyme_tail=target_entry.tail_d2, words=payload
        )

    else:
        # --- VERSE MODE: one genuine rhyme per scheme ---
        input_lower = text.lower().strip()
        verses = {}

        for scheme in ["AABB", "ABAB", "ABBA"]:
            suggestion = find_rhyming_verse(target_word, target_entry, seen_set, input_lower)
            if suggestion:
                seen_set.add(suggestion.line)  # avoid reuse across schemes
                verses[scheme] = suggestion
                print(f"   ✅ {scheme}: '{suggestion.line}' [rhyme: {suggestion.rhyme_word}]")
            else:
                print(f"   ❌ {scheme}: no matching verse found")

        return GenerationResponse(
            mode="verse", original_word=target_word,
            rhyme_tail=target_entry.tail_d2, verses=verses
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
