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

# --- Load vocabulary for word-level matching ---
def load_vocabulary():
    try:
        with open("words_pl.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if len(line.strip()) > 2]
    except FileNotFoundError:
        return []

# --- Load lyrics corpus and index lines by phonetic suffix ---
def load_lyrics_corpus(engine: PhoneticEngine):
    """Parse lyrics file, extract clean verse lines, index by phonetic suffix."""
    lines_d2 = defaultdict(list)  # tail_d2 -> [line, ...]
    lines_d1 = defaultdict(list)  # tail_d1 -> [line, ...]
    all_lines = []

    try:
        with open("lyrics_corrected.txt", "r", encoding="utf-8") as f:
            raw = f.readlines()
    except FileNotFoundError:
        return lines_d2, lines_d1, all_lines

    skip_patterns = re.compile(
        r'^\s*$|^\[|^#|^-{3,}|^\(|^Style:|^End|^Fade|^Finish'
    )

    for raw_line in raw:
        line = raw_line.strip()
        if not line or skip_patterns.match(line):
            continue
        # Clean brackets like [ha], [ey], [yeah] etc
        line_clean = re.sub(r'\[.*?\]', '', line).strip()
        if not line_clean or len(line_clean) < 10:
            continue

        words = line_clean.split()
        if not words:
            continue

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
    seen: Optional[List[str]] = []  # previously shown lines to avoid repeats

class VerseSuggestion(BaseModel):
    line: str
    rhyme_word: str
    grade: str
    score: float

class GenerationResponse(BaseModel):
    original_word: str
    original_verse: str
    suggestions: Dict[str, List[VerseSuggestion]]


# --- API ---
@app.post("/generate", response_model=GenerationResponse)
async def generate_rhymes(request: GenerationRequest):
    lines = request.verse.strip().split("\n")
    if not lines:
        raise HTTPException(status_code=400, detail="Empty verse")

    last_line = lines[-1].strip()
    words = last_line.split()
    if not words:
        raise HTTPException(status_code=400, detail="Empty line")

    target_word = re.sub(r'[^\w]', '', words[-1].lower())
    target_entry = engine.build_entry(target_word)

    seen_set = set(request.seen or [])

    # --- Find matching verse lines ---
    payload = {"PERFECT": [], "DOMINANT": [], "NEAR": []}

    # PERFECT: lines sharing tail_d2 (multi-syllable rhyme)
    perfect_lines = [l for l in LINES_D2.get(target_entry.tail_d2, [])
                     if l not in seen_set and l.lower() != last_line.lower()]
    random.shuffle(perfect_lines)
    for line in perfect_lines[:5]:
        rw = re.sub(r'[^\w]', '', line.split()[-1].lower())
        payload["PERFECT"].append(VerseSuggestion(
            line=line, rhyme_word=rw, grade="PERFECT", score=1.0
        ))

    # DOMINANT: lines sharing tail_d1 with high score, excluding perfects
    perfect_set = {s.line for s in payload["PERFECT"]}
    dominant_lines = [l for l in LINES_D1.get(target_entry.tail_d1, [])
                      if l not in seen_set and l not in perfect_set
                      and l.lower() != last_line.lower()]
    random.shuffle(dominant_lines)
    for line in dominant_lines[:5]:
        rw = re.sub(r'[^\w]', '', line.split()[-1].lower())
        payload["DOMINANT"].append(VerseSuggestion(
            line=line, rhyme_word=rw, grade="DOMINANT", score=0.8
        ))

    # NEAR: fallback from word-level engine if we need more
    if len(payload["PERFECT"]) + len(payload["DOMINANT"]) < 3:
        word_results = engine.find_candidates(target_word)
        shown_words = set()
        for word, grade, score in word_results:
            if word in shown_words:
                continue
            # Search corpus for lines ending with this word
            w_entry = engine.build_entry(word)
            candidates = LINES_D1.get(w_entry.tail_d1, [])
            for cand in candidates:
                cand_last = re.sub(r'[^\w]', '', cand.split()[-1].lower())
                if cand_last == word and cand not in seen_set:
                    payload["NEAR"].append(VerseSuggestion(
                        line=cand, rhyme_word=word, grade="NEAR", score=score
                    ))
                    shown_words.add(word)
                    break
            if len(payload["NEAR"]) >= 5:
                break

    return GenerationResponse(
        original_word=target_word,
        original_verse=last_line,
        suggestions=payload
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
