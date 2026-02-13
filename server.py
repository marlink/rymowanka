from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import re
from fastapi.middleware.cors import CORSMiddleware
from phonetic_engine import PhoneticEngine

app = FastAPI(title="Rhyme Architect API")

# Update CORS for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

def load_vocabulary():
    try:
        with open("words_pl.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if len(line.strip()) > 2]
    except FileNotFoundError:
        return ["miasto", "ciasto", "hasło", "jasno", "życie", "picie"]

# Initialize Engine with Vocabulary (Dependency Injection Pattern)
VOCABULARY = load_vocabulary()
engine = PhoneticEngine(VOCABULARY)

class GenerationRequest(BaseModel):
    verse: str

class RhymeSuggestion(BaseModel):
    word: str
    grade: str
    score: float

class GenerationResponse(BaseModel):
    original: str
    suggestions: Dict[str, List[RhymeSuggestion]]

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
    
    # O(k) Lookup
    raw_results = engine.find_candidates(target_word)
    
    # Group results
    payload = {"PERFECT": [], "DOMINANT": [], "NEAR": []}
    for word, grade, score in raw_results:
        if len(payload[grade]) < 10:
            payload[grade].append(RhymeSuggestion(word=word, grade=grade, score=score))

    return GenerationResponse(
        original=target_word,
        suggestions=payload
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
