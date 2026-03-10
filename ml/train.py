"""
train.py
--------
Master training script. Run this once to train and save all models.

Usage:
    python ml/train.py

What it does:
    1. Loads songs from data/processed/songs_features.csv
    2. Trains ContentBasedRecommender and saves to models/content_model.pkl
    3. Generates mock ratings (if no real ratings exist)
    4. Trains CollaborativeRecommender and saves to models/cf_model.pkl
    5. Runs a quick sanity check on the hybrid model
"""

import os
import sys
import pandas as pd

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.preprocessor import load_songs, generate_mock_ratings
from ml.content_based import ContentBasedRecommender
from ml.collaborative import CollaborativeRecommender
from ml.hybrid import HybridRecommender


def train():
    print("=" * 50)
    print("  Melodix — Model Training Pipeline")
    print("=" * 50)

    # ── Step 1: Load songs ──────────────────────────
    CSV_PATH = "data/processed/songs_features.csv"
    if not os.path.exists(CSV_PATH):
        print(f"\n❌ Songs CSV not found at {CSV_PATH}")
        print("   Run ml/data_collector.py first to fetch Spotify data.")
        print("   Or place a songs_features.csv with the required columns.")
        sys.exit(1)

    print(f"\n[1/4] Loading songs from {CSV_PATH}...")
    df = load_songs(CSV_PATH)
    print(f"      {len(df)} songs loaded")

    # ── Step 2: Content-based model ─────────────────
    print("\n[2/4] Training content-based model...")
    content_model = ContentBasedRecommender().fit(df)
    content_model.save("models/content_model.pkl")

    # ── Step 3: Ratings & collaborative model ───────
    RATINGS_PATH = "data/user_ratings.csv"
    if not os.path.exists(RATINGS_PATH):
        print("\n[3/4] No user_ratings.csv found — generating mock ratings...")
        ratings_df = generate_mock_ratings(df, n_users=300, ratings_per_user=25)
    else:
        print(f"\n[3/4] Loading ratings from {RATINGS_PATH}...")
        ratings_df = pd.read_csv(RATINGS_PATH)
        print(f"      {len(ratings_df)} ratings from {ratings_df['user_id'].nunique()} users")

    print("\n[4/4] Training collaborative filtering model...")
    cf_model = CollaborativeRecommender(n_factors=20).fit(ratings_df)
    cf_model.save("models/cf_model.pkl")

    # ── Sanity check ─────────────────────────────────
    print("\n" + "─" * 50)
    print("Sanity check: Hybrid recommendations")
    print("─" * 50)
    hybrid = HybridRecommender(content_model, cf_model, alpha=0.5)
    sample_id = df["id"].iloc[0]
    sample_title = df["title"].iloc[0]
    sample_artist = df["artist"].iloc[0]
    recs = hybrid.recommend(sample_id, user_id="user_0001", n=5)

    print(f"Seed: {sample_title} — {sample_artist}")
    print("Top 5 recommendations:")
    for i, (_, row) in enumerate(recs.iterrows(), 1):
        print(f"  {i}. {row['title']} — {row['artist']} (score: {row['hybrid_score']:.3f})")

    print("\n✅ All models trained and saved to models/")
    print("   Start the API server: uvicorn backend.main:app --reload")


if __name__ == "__main__":
    train()