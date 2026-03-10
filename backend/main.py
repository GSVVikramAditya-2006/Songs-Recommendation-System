"""
main.py
-------
FastAPI application entry point.

Start server:
    uvicorn backend.main:app --reload --port 8000

API docs (auto-generated):
    http://localhost:8000/docs
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Global model reference — loaded once at startup
hybrid_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models when the server starts."""
    global hybrid_model
    print("Melodix API starting up...")

    MODEL_PATH_CONTENT = "models/content_model.pkl"
    MODEL_PATH_CF = "models/cf_model.pkl"

    if not os.path.exists(MODEL_PATH_CONTENT):
        print(f"Model not found at {MODEL_PATH_CONTENT}")
        print("   Run: python ml/train.py")
        raise RuntimeError("Models not trained. Run ml/train.py first.")

    from ml.content_based import ContentBasedRecommender
    from ml.collaborative import CollaborativeRecommender
    from ml.hybrid import HybridRecommender
    from backend.database import init_db

    init_db()

    content_model = ContentBasedRecommender.load(MODEL_PATH_CONTENT)
    cf_model = None
    if os.path.exists(MODEL_PATH_CF):
        cf_model = CollaborativeRecommender.load(MODEL_PATH_CF)
        print("Loaded content-based + collaborative models")
    else:
        print("CF model not found, using content-based only")

    hybrid_model = HybridRecommender(content_model, cf_model, alpha=1.0)
    print(f"Hybrid model ready with {len(hybrid_model.df)} songs")
    yield
    print("Melodix API shutting down.")


app = FastAPI(
    title="Melodix — Song Recommendation API",
    description="Hybrid ML-powered song recommendations using content-based and collaborative filtering.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routes.songs import router as songs_router
from backend.routes.recommendations import router as rec_router

app.include_router(songs_router)
app.include_router(rec_router)


@app.get("/", tags=["health"])
def root():
    return {
        "app": "Melodix",
        "status": "running",
        "songs_loaded": len(hybrid_model.df) if hybrid_model else 0,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "model_ready": hybrid_model is not None}
