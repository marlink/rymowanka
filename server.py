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


def load_lyrics_corpus(engine: PhoneticEngine):
    """Index lyrics lines by phonetic suffix for verse-level matching."""
    lines_d2 = defaultdict(list)
    lines_d1 = defaultdict(list)
    all_lines = []

    try:
        with open("lyrics_corrected.txt", "r", encoding="utf-8") as f:
            raw = f.readlines()
    except FileNotFoundError:
        return lines_d2, lines_d1, all_lines

    skip = re.compile(r'^\s*$|^\[|^#|^-{3,}|^\(|^Style:|^End|^Fade|^Finish')

    for raw_line in raw:
        line = raw_line.strip()
        if not line or skip.match(line):
            continue
        line_clean = re.sub(r'\[.*?\]', '', line).strip()
        if not line_clean or len(line_clean) < 10:
            continue

        words = line_clean.split()
        last_word = re.sub(r'[^\w]', '', words[-1].lower())
        if len(last_word) < 2:
            continue

        entry = engine.build_entry(last_word)
        lines_d2[entry.tail_d2].append(line_clean)
        lines_d1[entry.tail_d1].append(line_clean)
        all_lines.append(line_clean)

    return lines_d2, lines_d1, all_lines


# --- Initialize ---
VOCABULARY = load_vocabulary()
engine = PhoneticEngine(VOCABULARY)
LINES_D2, LINES_D1, ALL_LINES = load_lyrics_corpus(engine)
print(f"📚 Indexed {len(ALL_LINES)} verse lines from lyrics corpus")


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
    mode: str  # "word" or "verse"
    original_word: str
    # Word mode
    words: Optional[Dict[str, List[WordSuggestion]]] = None
    # Verse mode
    verses: Optional[Dict[str, VerseSuggestion]] = None


def find_verse_suggestion(target_entry, seen_set: set, input_line: str):
    """Find one rhyming verse line from corpus, avoiding seen and input."""
    input_lower = input_line.lower().strip()

    # Try d2 (perfect match) first, then d1 (near)
    candidates = list(LINES_D2.get(target_entry.tail_d2, []))
    candidates += [l for l in LINES_D1.get(target_entry.tail_d1, [])
                   if l not in candidates]

    # Shuffle for variety
    random.shuffle(candidates)

    for line in candidates:
        if line in seen_set and line.lower().strip() != input_lower:
            continue
        if line.lower().strip() == input_lower:
            continue
        if line in seen_set:
            continue
        rw = re.sub(r'[^\w]', '', line.split()[-1].lower())
        # Calculate score
        rw_entry = engine.build_entry(rw)
        is_d2 = rw_entry.tail_d2 == target_entry.tail_d2
        score = engine.score(target_entry, rw_entry, is_d2)
        return VerseSuggestion(line=line, rhyme_word=rw, score=score)

    return None


@app.post("/generate", response_model=GenerationResponse)
async def generate_rhymes(request: GenerationRequest):
    text = request.verse.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty input")

    seen_set = set(request.seen or [])
    words = text.split()
    is_single_word = len(words) == 1

    target_word = re.sub(r'[^\w]', '', words[-1].lower())
    target_entry = engine.build_entry(target_word)

    if is_single_word:
        # --- WORD MODE: return rhyming words ---
        raw_results = engine.find_candidates(target_word)
        payload = {"PERFECT": [], "DOMINANT": [], "NEAR": []}
        for word, grade, score in raw_results:
            if len(payload[grade]) < 10:
                payload[grade].append(WordSuggestion(word=word, grade=grade, score=score))

        return GenerationResponse(
            mode="word",
            original_word=target_word,
            words=payload
        )
    else:
        # --- VERSE MODE: one suggestion per rhyme scheme ---
        verses = {}
        for scheme in ["AABB", "ABAB", "ABBA"]:
            suggestion = find_verse_suggestion(target_entry, seen_set, text)
            if suggestion:
                seen_set.add(suggestion.line)  # don't reuse across schemes
                verses[scheme] = suggestion

        return GenerationResponse(
            mode="verse",
            original_word=target_word,
            verses=verses
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
