"""
content_based.py
----------------
Content-based filtering using cosine similarity on audio features.

How it works:
  1. Each song is represented as a vector of audio features
  2. Given a query song, we compute cosine similarity to all other songs
  3. Return the top-N most similar songs

Audio features used:
  danceability, energy, valence, tempo, acousticness,
  instrumentalness, liveness, speechiness, loudness
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os

from ml.preprocessor import load_songs, build_feature_matrix, CONTENT_FEATURES


class ContentBasedRecommender:
    def __init__(self):
        self.df = None          # Song dataframe
        self.X = None           # Feature matrix (normalized)
        self.song_id_to_idx = {}

    def fit(self, df: pd.DataFrame):
        """Train the model: build and store the feature matrix."""
        self.df = df.reset_index(drop=True)
        self.X, self.scaler = build_feature_matrix(self.df)
        self.song_id_to_idx = {sid: i for i, sid in enumerate(self.df["id"])}
        print(f"✅ ContentBased: fitted on {len(self.df)} songs, {self.X.shape[1]} features")
        return self

    def recommend(self, song_id: str, n: int = 10) -> pd.DataFrame:
        """
        Returns top-N similar songs for a given song_id.
        Returns a DataFrame with columns: id, title, artist, similarity_score
        """
        if song_id not in self.song_id_to_idx:
            raise ValueError(f"Song ID '{song_id}' not found in dataset")

        idx = self.song_id_to_idx[song_id]
        query_vec = self.X[idx].reshape(1, -1)

        # Compute cosine similarity to all songs
        sims = cosine_similarity(query_vec, self.X).flatten()
        sims[idx] = -1  # Exclude the query song itself
# Only return from top 5000 most popular songs for speed
        if len(sims) > 5000:
            bottom_indices = np.argsort(sims)[:-5000]
            sims[bottom_indices] = -1        

        # Get top-N indices
        top_indices = np.argsort(sims)[::-1][:n]

        results = self.df.iloc[top_indices].copy()
        results["content_score"] = sims[top_indices]
        return results[["id", "title", "artist", "album", "album_cover",
                         "preview_url", "popularity", "content_score"] +
                        CONTENT_FEATURES]

    def get_song_features(self, song_id: str) -> dict:
        """Returns the normalized feature vector for a song."""
        if song_id not in self.song_id_to_idx:
            raise ValueError(f"Song ID '{song_id}' not found")
        idx = self.song_id_to_idx[song_id]
        features = {k: float(self.X[idx][i]) for i, k in enumerate(CONTENT_FEATURES)}
        return features

    def save(self, path="models/content_model.pkl"):
        os.makedirs("models", exist_ok=True)
        joblib.dump(self, path)
        print(f"✅ Content model saved to {path}")

    @classmethod
    def load(cls, path="models/content_model.pkl"):
        return joblib.load(path)


if __name__ == "__main__":
    df = load_songs()
    model = ContentBasedRecommender().fit(df)
    model.save()

    # Quick test
    sample_id = df["id"].iloc[0]
    recs = model.recommend(sample_id, n=5)
    print(f"\nTop 5 recommendations for: {df['title'].iloc[0]}")
    for _, row in recs.iterrows():
        print(f"  {row['title']} — {row['artist']} (score: {row['content_score']:.3f})")
