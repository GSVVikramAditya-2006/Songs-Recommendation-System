# 🎵 Melodix — Hybrid ML Song Recommendation System

A full-stack music recommendation engine using a **hybrid ML model** (content-based + collaborative filtering) with a React frontend and FastAPI backend.

---

## Architecture

```
Spotify API → data_collector.py → songs_features.csv
                                        ↓
                              preprocessor.py (normalize)
                              ↙                    ↘
              content_based.py              collaborative.py
            (cosine similarity)             (SVD via Surprise)
                              ↘                    ↙
                               hybrid.py (α blend)
                                      ↓
                            FastAPI backend (port 8000)
                                      ↓
                            React frontend (port 3000)
```

---

## Project Structure

```
song-recommender/
├── ml/
│   ├── data_collector.py     # Fetch songs from Spotify API
│   ├── preprocessor.py       # Clean & normalize features
│   ├── content_based.py      # Cosine similarity model
│   ├── collaborative.py      # SVD collaborative filtering
│   ├── hybrid.py             # Blend both models
│   └── train.py              # Master training script
├── backend/
│   ├── main.py               # FastAPI app
│   ├── database.py           # SQLite via SQLAlchemy
│   ├── schemas.py            # Pydantic models
│   └── routes/
│       ├── songs.py          # Search & detail endpoints
│       └── recommendations.py # Recommend & rate endpoints
├── frontend/
│   └── src/
│       ├── App.jsx           # Main UI
│       ├── components/
│       │   ├── SongCard.jsx
│       │   └── AudioFeatures.jsx
│       └── api/client.js     # Axios API client
├── notebooks/
│   └── 01_exploration.ipynb
├── data/
│   ├── raw/                  # Raw Spotify data
│   ├── processed/            # Feature CSVs
│   └── user_ratings.csv      # Ratings for CF training
└── models/
    ├── content_model.pkl
    └── cf_model.pkl
```

---

## Quick Start

### 1. Clone & Install Python deps

```bash
git clone <your-repo>
cd song-recommender
pip install -r requirements.txt
```

### 2. Set up Spotify API credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app → copy Client ID and Client Secret
3. Create your `.env` file:

```bash
cp .env.example .env
# Edit .env and add your credentials
```

### 3. Collect data & train models

```bash
# Fetch songs from Spotify (requires credentials)
python ml/data_collector.py

# Train all models (also generates mock ratings if none exist)
python ml/train.py
```

> **No Spotify credentials?** You can skip `data_collector.py` and manually create
> `data/processed/songs_features.csv` with columns:
> `id, title, artist, album, album_cover, preview_url, popularity,`
> `danceability, energy, valence, tempo, acousticness, instrumentalness,`
> `liveness, speechiness, loudness, tempo_normalized, loudness_normalized`

### 4. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/songs/all` | List all songs |
| GET | `/songs/search?q=...` | Search songs |
| GET | `/songs/{id}` | Song detail + features |
| POST | `/recommend` | Get recommendations |
| POST | `/recommend/rate` | Submit a rating |
| GET | `/recommend/history/{user_id}` | User history |

### Example: Get recommendations

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"song_id": "3n3Ppam7vgaVa1iaRUIOKE", "user_id": "user_001", "n": 10}'
```

---

## How the ML Works

### Content-Based (50% weight)
- Represents each song as a 9-dimensional vector of audio features
- Computes **cosine similarity** between the seed song and all others
- Pure audio math — no user data needed (solves cold-start problem)

### Collaborative Filtering (50% weight)
- Uses **SVD** (Singular Value Decomposition) to find latent user-song patterns
- "Users like you also liked..." style recommendations
- Requires user ratings — gets better over time

### Hybrid Blending
```python
hybrid_score = α * content_score + (1 - α) * cf_score
```
- Default `α = 0.5` (equal weight)
- If no user data → `α = 1.0` (falls back to pure content-based)
- Tune α in `ml/hybrid.py`

---

## Next Steps / Improvements

- [ ] Add user authentication (JWT)
- [ ] Re-train models incrementally as new ratings come in
- [ ] Add genre filtering
- [ ] Deploy to Railway/Render (backend) + Vercel (frontend)
- [ ] Replace mock ratings with real user data
- [ ] Try neural CF (NeuMF) for better collaborative filtering
