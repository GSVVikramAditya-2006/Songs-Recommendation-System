# Melodix — Hybrid ML Song Recommendation System

A full-stack music recommendation engine using a hybrid ML model (content-based + collaborative filtering) with a React frontend and FastAPI backend.

---

## How It Works — Full Explanation

### The Big Picture

```
You (Browser) <-> React Frontend <-> FastAPI Backend <-> ML Models <-> Song Data
```

### 1. Data Layer — `data/processed/songs_features.csv`

Every song is represented as a vector of 9 audio features measured by Spotify:

| Feature | What it means |
|---------|--------------|
| Energy | How intense/loud the song feels |
| Danceability | How suitable for dancing |
| Valence | How happy/positive it sounds |
| Tempo | Speed in BPM (normalized to 0-1) |
| Acousticness | How acoustic vs electronic |
| Instrumentalness | How little vocals there are |
| Liveness | Whether it sounds like a live recording |
| Speechiness | How much spoken word |
| Loudness | Overall volume (normalized) |

For example:
```
Blinding Lights -> [0.73, 0.51, 0.33, 0.87, 0.0, 0.0, 0.09, 0.06, 0.75]
```

### 2. ML Training — `ml/train.py`

Two models are trained and saved:

**Content-Based Model (`ml/content_based.py`)**
- Loads all song vectors into a matrix
- When you request recommendations for Song A, it computes cosine similarity between Song A's vector and every other song's vector
- Cosine similarity measures the angle between two vectors — songs pointing in the same direction are similar
- Returns the top N most similar songs
- Saved to `models/content_model.pkl`

**Collaborative Filtering Model (`ml/collaborative.py`)**
- Builds a User x Song rating matrix
- Runs SVD (Singular Value Decomposition) to find hidden patterns — e.g. "users who like energetic songs also like high-tempo songs"
- Can predict what rating any user would give any song
- Saved to `models/cf_model.pkl`

**Hybrid Model (`ml/hybrid.py`)**
- Combines both models: `score = alpha * content_score + (1 - alpha) * cf_score`
- Default `alpha = 1.0` (pure content-based until real user data accumulates)
- As users rate/like songs, lower alpha to blend in collaborative signals

### 3. Backend — `backend/main.py`

FastAPI server running on port 8000. On startup it loads both trained models into memory and exposes these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/songs/all` | Paginated list of all songs |
| GET | `/songs/search?q=...` | Search songs by name or artist |
| GET | `/songs/{id}` | One song with full audio features |
| POST | `/recommend` | Get recommendations for a song |
| POST | `/recommend/rate` | Save a user rating to SQLite |
| GET | `/recommend/history/{user_id}` | User's listening history |

### 4. Frontend — `frontend/src/App.jsx`

React app running on port 3000:

- **On load** — fetches first 100 songs from `/songs/all`. As you scroll down it loads the next 100 (infinite scroll), but recommendations always come from all songs in the dataset
- **Click a song** — fetches full audio features, renders radar chart and feature bars
- **Similar Songs button** — calls `POST /recommend`, backend runs cosine similarity across all songs, returns top 10
- **Heart a song** — saves to React state + calls `POST /recommend/rate` with rating 5
- **Recommend from Likes** — averages audio features of all liked songs to build a taste profile, finds the liked song closest to that average, uses it as seed for recommendations, filters out already-liked songs

### 5. The Full Journey of One Recommendation

```
You click "Similar Songs" on a track
        |
React sends POST /recommend {song_id: "xyz"}
        |
FastAPI receives request
        |
hybrid.py calls content_based.recommend("xyz", n=10)
        |
Looks up the song's feature vector
        |
Computes cosine similarity vs all songs in dataset
        |
Sorts by similarity, returns top 10
        |
hybrid.py blends with CF score (currently 0% weight)
        |
FastAPI returns JSON to React
        |
React renders 10 song cards with match % in right panel
```

### 6. The Library vs Recommendations

- **Library panel** — shows 100 songs at a time (scroll to load more) for display performance
- **Search bar** — searches all songs in the dataset instantly via backend
- **Recommendations** — always computed from the entire dataset, not just loaded songs

---

## Project Structure

```
song-recommender/
|-- ml/
|   |-- data_collector.py     # Fetch songs from Spotify API
|   |-- preprocessor.py       # Clean, normalize features, generate mock ratings
|   |-- content_based.py      # Cosine similarity model
|   |-- collaborative.py      # SVD collaborative filtering (pure numpy)
|   |-- hybrid.py             # Blend both models with alpha weighting
|   `-- train.py              # Master training script
|-- backend/
|   |-- main.py               # FastAPI app entry point
|   |-- database.py           # SQLite via SQLAlchemy (ratings + history)
|   |-- schemas.py            # Pydantic request/response models
|   `-- routes/
|       |-- songs.py          # /songs endpoints
|       `-- recommendations.py # /recommend endpoints
|-- frontend/
|   `-- src/
|       |-- App.jsx           # Main UI with likes, search, infinite scroll
|       |-- components/
|       |   |-- SongCard.jsx
|       |   `-- AudioFeatures.jsx  # Radar chart + feature bars
|       `-- api/client.js     # Axios API client
|-- notebooks/
|   `-- 01_exploration.ipynb  # Data exploration and model testing
|-- data/
|   |-- processed/            # songs_features.csv
|   `-- user_ratings.csv      # Ratings used for CF training
|-- models/
|   |-- content_model.pkl     # Trained content-based model
|   `-- cf_model.pkl          # Trained collaborative model
|-- prepare_data.py           # Convert Kaggle CSV to project format
|-- requirements.txt
`-- .env.example
```

---

## Quick Start

### 1. Clone and install dependencies

```bash
git clone <your-repo>
cd song-recommender
pip install -r requirements.txt
```

### 2. Get a dataset

Download the Spotify Tracks Dataset from Kaggle:
https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset

Place `dataset.csv` in the project root, then run:

```bash
python prepare_data.py
```

This converts and filters the dataset, saving to `data/processed/songs_features.csv`.

### 3. Train the models

```bash
python ml/train.py
```

This trains both the content-based and collaborative models and saves them to `models/`.

### 4. Start the backend

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 5. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

---

## Dependencies

**Python:**
```
pandas, numpy, scikit-learn, fastapi, uvicorn, sqlalchemy, pydantic, python-dotenv, joblib
```

**Node:**
```
react, react-dom, axios, recharts, react-router-dom, vite
```

---

## Tuning the Hybrid Model

Edit `alpha` in `backend/main.py`:

```python
hybrid_model = HybridRecommender(content_model, cf_model, alpha=1.0)
```

- `alpha = 1.0` — pure content-based (good when starting out, no real user data)
- `alpha = 0.5` — equal blend of content + collaborative
- `alpha = 0.0` — pure collaborative (only when you have lots of real ratings)

---

## Improving Recommendation Quality

The dataset includes podcasts, audiobooks, and comedy albums. Filter them out in `prepare_data.py` for better music-only recommendations:

```python
df = df[df["speechiness"] < 0.5]   # Remove podcasts/comedy
df = df[df["popularity"] > 20]      # Keep reasonably known songs
```

Then retrain: `python ml/train.py`

---

## Next Steps

- [ ] Add user authentication (JWT)
- [ ] Retrain collaborative model periodically on real user ratings
- [ ] Add genre/mood filtering
- [ ] Deploy backend to Railway or Render
- [ ] Deploy frontend to Vercel
- [ ] Try neural collaborative filtering (NeuMF) for better personalization
