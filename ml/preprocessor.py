"""
preprocessor.py
---------------
Cleans and normalizes song features for use in ML models.
Outputs a feature matrix ready for cosine similarity and SVD.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

# These are the features used for content-based similarity
CONTENT_FEATURES = [
    "danceability", "energy", "valence",
    "tempo_normalized", "acousticness",
    "instrumentalness", "liveness", "speechiness",
    "loudness_normalized",
]


def load_songs(path="data/processed/songs_features.csv"):
    df = pd.read_csv(path)
    df = df.dropna(subset=CONTENT_FEATURES)
    df = df.drop_duplicates(subset=["id"])
    df = df.reset_index(drop=True)
    return df


def build_feature_matrix(df):
    """
    Returns a normalized feature matrix (numpy array) and the scaler.
    Each row = one song. Each column = one audio feature.
    """
    X = df[CONTENT_FEATURES].values.astype(float)
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, scaler


def generate_mock_ratings(df, n_users=200, ratings_per_user=20, seed=42):
    """
    Generates synthetic user-song ratings for collaborative filtering training.
    In production, replace this with real user interaction data.

    Rating logic: users prefer songs similar to a randomly picked "taste profile".
    """
    rng = np.random.default_rng(seed)
    X, _ = build_feature_matrix(df)
    song_ids = df["id"].tolist()
    n_songs = len(song_ids)

    rows = []
    for user_id in range(n_users):
        # Each user has a random taste vector
        taste = rng.random(X.shape[1])
        # Compute similarity of all songs to this taste
        sims = X @ taste / (np.linalg.norm(X, axis=1) * np.linalg.norm(taste) + 1e-9)
        # Pick top songs with some randomness
        noisy_sims = sims + rng.normal(0, 0.1, n_songs)
        top_indices = np.argsort(noisy_sims)[-ratings_per_user:]
        for idx in top_indices:
            # Rating 1-5: higher similarity → higher rating, with noise
            raw = noisy_sims[idx]
            rating = float(np.clip(rng.normal(raw * 5, 0.5), 1, 5))
            rows.append({
                "user_id": f"user_{user_id:04d}",
                "song_id": song_ids[idx],
                "rating": round(rating, 1),
            })

    ratings_df = pd.DataFrame(rows)
    os.makedirs("data", exist_ok=True)
    ratings_df.to_csv("data/user_ratings.csv", index=False)
    print(f"✅ Generated {len(ratings_df)} ratings for {n_users} users")
    return ratings_df


def save_scaler(scaler, path="models/scaler.pkl"):
    os.makedirs("models", exist_ok=True)
    joblib.dump(scaler, path)


def load_scaler(path="models/scaler.pkl"):
    return joblib.load(path)


if __name__ == "__main__":
    print("Loading songs...")
    df = load_songs()
    print(f"  {len(df)} songs loaded")

    print("Building feature matrix...")
    X, scaler = build_feature_matrix(df)
    save_scaler(scaler)
    print(f"  Feature matrix shape: {X.shape}")

    print("Generating mock ratings...")
    generate_mock_ratings(df)
