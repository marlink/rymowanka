"""
Centralized configuration and shared singleton instances.
"""
import os
from phonetic_engine import PhoneticEngine

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCABULARY_PATH = os.getenv("VOCABULARY_PATH", os.path.join(BASE_DIR, "words_pl.txt"))
LYRICS_PATH = os.getenv("LYRICS_PATH", os.path.join(BASE_DIR, "lyrics_corrected.txt"))

# --- Server ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# --- Limits ---
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "500"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))


def _load_vocabulary() -> list[str]:
    try:
        with open(VOCABULARY_PATH, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if len(line.strip()) > 2]
    except FileNotFoundError:
        return []


# --- Singleton shared engine ---
VOCABULARY = _load_vocabulary()
ENGINE = PhoneticEngine(VOCABULARY)
