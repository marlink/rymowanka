from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import time
import re
import random
from collections import defaultdict
from fastapi.middleware.cors import CORSMiddleware
from config import ENGINE, LYRICS_PATH, CORS_ORIGINS, MAX_INPUT_LENGTH, RATE_LIMIT_PER_MINUTE, WORD_SCORES

app = FastAPI(title="Rhyme Architect API")

# --- Rate Limiting ---
RATE_LIMIT_DATA = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    RATE_LIMIT_DATA[client_ip] = [t for t in RATE_LIMIT_DATA[client_ip] if t > now - 60]
    
    if len(RATE_LIMIT_DATA[client_ip]) >= RATE_LIMIT_PER_MINUTE:
         return Response(content="Rate limit exceeded", status_code=429)
    
    RATE_LIMIT_DATA[client_ip].append(now)
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "online", "engine": "PhoneticEngine", "corpus_size": len(ALL_LINES)}

# --- Junk filter for word-mode results ---
JUNK_RE = re.compile(r'[-.]|^[a-z]{1,3}-|^\w+-\w+$')


def is_clean_word(w: str) -> bool:
    """Filter abbreviations, hyphenated garbage, transliterations."""
    if JUNK_RE.search(w):
        return False
    if len(w) < 3:
        return False
    return True


def clean_last_word(text: str) -> str:
    words = text.strip().split()
    if not words:
        return ""
    return re.sub(r'[^\w]', '', words[-1].lower())


def count_syllables(text: str) -> int:
    """Count syllables in a line using engine's vowel detection."""
    total = 0
    for word in text.split():
        clean = re.sub(r'[^\w]', '', word.lower())
        if not clean:
            continue
        norm = ENGINE.normalize(clean)
        total += max(len(ENGINE.get_vowel_positions(norm)), 1)
    return total


def load_lyrics_corpus():
    lines_by_d2 = defaultdict(list)
    lines_by_word = defaultdict(list)
    all_lines = []

    try:
        with open(LYRICS_PATH, "r", encoding="utf-8") as f:
            raw = f.readlines()
    except FileNotFoundError:
        print(f"⚠️ Warning: Lyrics corpus not found at {LYRICS_PATH}")
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

        entry = ENGINE.build_entry(last)
        lines_by_d2[entry.tail_d2].append(line_clean)
        lines_by_word[last].append(line_clean)
        all_lines.append(line_clean)

    return lines_by_d2, lines_by_word, all_lines


# --- Initialize ---
LINES_BY_D2, LINES_BY_WORD, ALL_LINES = load_lyrics_corpus()
print(f"📚 Corpus: {len(ALL_LINES)} lines, {len(LINES_BY_D2)} unique rhyme tails")


# --- Models ---
class GenerationRequest(BaseModel):
    verse: str
    seen: Optional[List[str]] = []

class WordSuggestion(BaseModel):
    word: str
    grade: str
    score: float
    flags: List[str] = []

class VerseSuggestion(BaseModel):
    line: str
    rhyme_word: str
    score: float
    syllables: int

class GenerationResponse(BaseModel):
    mode: str
    original_word: str
    rhyme_tail: str
    input_syllables: Optional[int] = None
    words: Optional[Dict[str, List[WordSuggestion]]] = None
    verses: Optional[List[VerseSuggestion]] = None


def find_rhyming_verses(target_word: str, target_entry, seen_set: set,
                        input_lower: str, input_syllables: int, limit: int = 5):
    """Find corpus lines that genuinely rhyme. Sorted by quality + syllable match."""
    results = []

    # Strategy 1: Direct d2 corpus lookup
    d2_candidates = list(LINES_BY_D2.get(target_entry.tail_d2, []))
    random.shuffle(d2_candidates)

    for line in d2_candidates:
        if line.lower().strip() == input_lower or line in seen_set:
            continue
        rw = clean_last_word(line)
        if rw == target_word:
            continue
        syl = count_syllables(line)
        syl_diff = abs(syl - input_syllables)
        # Score: base 1.0, penalize syllable mismatch
        score = max(1.0 - (syl_diff * 0.08), 0.5)
        results.append(VerseSuggestion(line=line, rhyme_word=rw, score=score, syllables=syl))

    # Strategy 2: Dictionary rhyme words → corpus lines
    rhyming_words = ENGINE.find_candidates(target_word)
    perfect_words = [w for w, grade, sc in rhyming_words if grade == "PERFECT"]
    random.shuffle(perfect_words)

    existing_lines = {r.line for r in results}
    for rw in perfect_words:
        for line in LINES_BY_WORD.get(rw, []):
            if line in existing_lines or line.lower().strip() == input_lower or line in seen_set:
                continue
            syl = count_syllables(line)
            syl_diff = abs(syl - input_syllables)
            score = max(0.9 - (syl_diff * 0.08), 0.4)
            results.append(VerseSuggestion(line=line, rhyme_word=rw, score=score, syllables=syl))
            existing_lines.add(line)

    # Sort: best rhyme + closest syllable count first
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]


@app.post("/generate", response_model=GenerationResponse)
async def generate_rhymes(request: GenerationRequest):
    if len(request.verse) > MAX_INPUT_LENGTH:
         raise HTTPException(status_code=400, detail=f"Input too long (max {MAX_INPUT_LENGTH} chars)")

    text = request.verse.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty input")

    seen_set = set(request.seen or [])
    target_word = clean_last_word(text)
    if not target_word:
        raise HTTPException(status_code=400, detail="No valid word found")

    target_entry = ENGINE.build_entry(target_word)
    is_single_word = len(text.split()) == 1

    print(f"🔍 '{text}' → word='{target_word}' tail='{target_entry.tail_d2}' mode={'word' if is_single_word else 'verse'}")

    if is_single_word:
        raw_results = ENGINE.find_candidates(target_word)
        # Apply prioritization scores
        processed = []
        for word, grade, base_score in raw_results:
            if not is_clean_word(word):
                continue
            
            # Boost score based on our quality mapping
            meta = WORD_SCORES.get(word, {})
            # Handle both old float format (if any legacy cache) and new dict format
            if isinstance(meta, float):
                priority = meta
                flags = []
            else:
                priority = meta.get("s", 0.5)
                flags = meta.get("f", [])

            final_score = base_score * priority
            processed.append((word, grade, final_score, flags))
            
        # Sort by grade first, then by the boosted score
        processed.sort(key=lambda x: (x[1] != "PERFECT", x[1] != "DOMINANT", -x[2]))

        payload = {"PERFECT": [], "DOMINANT": [], "NEAR": []}
        for word, grade, score, flags in processed:
            if len(payload[grade]) < 15: # Increased limit slightly to show variety
                payload[grade].append(WordSuggestion(word=word, grade=grade, score=score, flags=flags))
        
        return GenerationResponse(
            mode="word", original_word=target_word,
            rhyme_tail=target_entry.tail_d2, words=payload
        )
    else:
        input_syl = count_syllables(text)
        verses = find_rhyming_verses(
            target_word, target_entry, seen_set, text.lower().strip(), input_syl
        )
        for v in verses:
            print(f"   ✅ [{v.syllables}syl] {v.line}")
        if not verses:
            print(f"   ❌ No rhyming verses found")

        return GenerationResponse(
            mode="verse", original_word=target_word,
            rhyme_tail=target_entry.tail_d2,
            input_syllables=input_syl, verses=verses
        )


if __name__ == "__main__":
    from config import PORT
    uvicorn.run(app, host="0.0.0.0", port=PORT)
