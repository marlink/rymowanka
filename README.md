## Deployment (Option 2: Hybrid)

### 1. Backend (Render.com)
1. Fork/Clone this repo to GitHub.
2. Sign up for **Render.com**.
3. Create "New Web Service".
4. Connect your repo.
5. Runtime: **Docker** (it will auto-detect `Dockerfile`).
6. **Environment Variables**:
   - `CORS_ORIGINS`: `https://your-frontend.vercel.app` (add after deploying frontend)
7. Click **Deploy**.

### 2. Frontend (Vercel)
1. Sign up for **Vercel**.
2. "Add New..." -> Project.
3. Import your repo.
4. **Root Directory**: Select `frontend` folder (Edit).
5. **Framework Preset**: Vite (Auto-detected).
6. **Environment Variables**:
   - `VITE_API_URL`: `https://your-render-app.onrender.com` (from step 1)
7. Click **Deploy**.


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
