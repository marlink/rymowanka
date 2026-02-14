## Deployment (Option 2: Hybrid)

### 1. Backend (Railway.app)
1. Sign up/Log in to [Railway.app](https://railway.app).
2. **New Project** → **Deploy from GitHub repo**.
3. Select this repository.
4. Railway detects the root `Dockerfile` and deploys automatically.
5. **Variables**: Add `CORS_ORIGINS` = `https://your-frontend.vercel.app`.

### 2. Frontend (Vercel)
1. Import repo to [Vercel](https://vercel.com).
2. **Root Directory**: Set to `frontend`.
3. **Variables**: Add `VITE_API_URL` = `https://your-railway-url.up.railway.app`.
4. Deploy.


```
┌─────────────────────┐        POST /generate        ┌──────────────────┐
│  Frontend (Vite)    │ ──────────────────────────▶  │  server.py       │
│  localhost:5173      │ ◀──────────────────────────  │  FastAPI :8000   │
└─────────────────────┘        JSON response          └────────┬─────────┘
                                                               │
                                                    ┌──────────▼──────────┐
                                                    │  PhoneticEngine     │
                                                    │  phonetic_engine.py │
                                                    └─────────────────────┘
                                                    ┌─────────────────────┐
                                                    │  words_pl.txt       │  ← ~50k word vocabulary
                                                    │  lyrics_corrected   │  ← rap lyrics corpus
                                                    └─────────────────────┘
```

### Modules

| File | Purpose |
|---|---|
| `phonetic_engine.py` | Core — normalizes Polish words to phonetic form, builds rhyme index (tail_d2/d1), scores candidates |
| `server.py` | FastAPI server — word mode (graded lists) and verse mode (corpus line matching) |
| `polish_rhyme_util.py` | Utility — syllable counting, phonetic suffix extraction, rhyme scheme verification |
| `context_agent.py` | Heuristic semantic flow checker (thematic clusters, connectors) |
| `polish_engine.py` | Legacy CLI demo of AABB/ABAB/ABBA rhyme schemes |
| `test_blueprints.py` | Tests rhyme scheme verification against `blueprint_tests.json` |
| `test_verse.py` | Quick stanza verification script |
| `frontend/` | Vite + Vanilla JS/CSS — "Tech-Noir" dark UI |

## Setup

```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn
python server.py                     # → localhost:8000

# Frontend
cd frontend && npm install && npm run dev  # → localhost:5173
```

## API

### `POST /generate`

**Request:**
```json
{ "verse": "Idę przez miasto nocą", "seen": [] }
```

**Response (verse mode):**
```json
{
  "mode": "verse",
  "original_word": "nocą",
  "rhyme_tail": "ocą",
  "input_syllables": 7,
  "verses": [
    { "line": "Myśli krążą nad złotą obwodnicą", "rhyme_word": "obwodnicą", "score": 0.84, "syllables": 8 }
  ]
}
```

Single-word input returns `"mode": "word"` with `words: { PERFECT: [...], DOMINANT: [...], NEAR: [...] }`.

## Data Files

- **`words_pl.txt`** (~1 MB) — Polish vocabulary, filtered to 3+ char words
- **`words_pl_full.txt`** (~3.7 MB) — Full unfiltered vocabulary
- **`lyrics_corrected.txt`** (~39 KB) — Curated rap lyrics corpus
- **`blueprint_tests.json`** (~18 KB) — Test stanzas for rhyme scheme validation
