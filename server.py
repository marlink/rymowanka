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
    """Index lyrics lines by their last word for lookup."""
    # last_word_normalized -> [line, ...]
    lines_by_word = defaultdict(list)
    # tail_d2 -> [line, ...]
    lines_by_d2 = defaultdict(list)
    all_lines = []

    try:
        with open("lyrics_corrected.txt", "r", encoding="utf-8") as f:
            raw = f.readlines()
    except FileNotFoundError:
        return lines_by_word, lines_by_d2, all_lines

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
        lines_by_word[last_word].append(line_clean)
        lines_by_d2[entry.tail_d2].append(line_clean)
        all_lines.append(line_clean)

    return lines_by_word, lines_by_d2, all_lines


# --- Initialize ---
VOCABULARY = load_vocabulary()
engine = PhoneticEngine(VOCABULARY)
LINES_BY_WORD, LINES_BY_D2, ALL_LINES = load_lyrics_corpus(engine)
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
    words: Optional[Dict[str, List[WordSuggestion]]] = None
    verses: Optional[Dict[str, VerseSuggestion]] = None


def find_rhyming_verse(target_word: str, seen_set: set, input_line: str):
    """
    Find a corpus line that genuinely rhymes with target_word.
    Strategy:
      1. Direct d2 (multi-syllable suffix) lookup in corpus index
      2. Use word engine to find rhyming words, then find corpus lines ending with them
    Only returns lines where the last word has matching tail_d2 (real rhyme).
    """
    target_entry = engine.build_entry(target_word)
    input_lower = input_line.lower().strip()

    # --- Strategy 1: Direct corpus d2 lookup ---
    d2_candidates = list(LINES_BY_D2.get(target_entry.tail_d2, []))
    random.shuffle(d2_candidates)

    for line in d2_candidates:
        if line.lower().strip() == input_lower:
            continue
        if line in seen_set:
            continue
        rw = re.sub(r'[^\w]', '', line.split()[-1].lower())
        if rw == target_word:
            continue  # don't suggest same word
        return VerseSuggestion(line=line, rhyme_word=rw, score=1.0)

    # --- Strategy 2: Find rhyming words from dictionary, then match to corpus ---
    rhyming_words = engine.find_candidates(target_word)
    # Only use PERFECT matches (d2 match = real rhyme)
    perfect_words = [w for w, grade, score in rhyming_words if grade == "PERFECT"]
    random.shuffle(perfect_words)

    for rw in perfect_words:
        corpus_lines = LINES_BY_WORD.get(rw, [])
        random.shuffle(corpus_lines)
        for line in corpus_lines:
            if line.lower().strip() == input_lower:
                continue
            if line in seen_set:
                continue
            return VerseSuggestion(line=line, rhyme_word=rw, score=0.9)

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

    if is_single_word:
        # --- WORD MODE ---
        raw_results = engine.find_candidates(target_word)
        payload = {"PERFECT": [], "DOMINANT": [], "NEAR": []}
        for word, grade, score in raw_results:
            if len(payload[grade]) < 10:
                payload[grade].append(WordSuggestion(word=word, grade=grade, score=score))
        return GenerationResponse(mode="word", original_word=target_word, words=payload)

    else:
        # --- VERSE MODE: one genuine rhyme per scheme ---
        verses = {}
        for scheme in ["AABB", "ABAB", "ABBA"]:
            suggestion = find_rhyming_verse(target_word, seen_set, text)
            if suggestion:
                seen_set.add(suggestion.line)
                verses[scheme] = suggestion
        return GenerationResponse(mode="verse", original_word=target_word, verses=verses)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
