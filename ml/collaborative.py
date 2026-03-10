"""
collaborative.py
----------------
Collaborative filtering using pure SVD via numpy (no scikit-surprise needed).

How it works:
  1. Build a user x song rating matrix
  2. Decompose it with truncated SVD (numpy) to find latent factors
  3. Reconstruct predicted ratings for all user-song pairs
  4. For a given user, return top-N unheard songs by predicted rating

Key concept: SVD finds hidden patterns — users who rate energetic songs highly
tend to also rate high-tempo songs highly, without us explicitly telling it that.
"""

import pandas as pd
import numpy as np
import joblib
import os


class CollaborativeRecommender:
    def __init__(self, n_factors=20):
        """
        n_factors: Number of latent dimensions to keep after SVD.
                   Higher = more expressive but slower. 20 is a good default.
        """
        self.n_factors = n_factors
        self.user_factors = None    # U matrix from SVD
        self.song_factors = None    # Vt matrix from SVD
        self.sigma = None           # Singular values
        self.user_index = {}        # user_id -> row index
        self.song_index = {}        # song_id -> col index
        self.song_ids = []          # col index -> song_id
        self.user_means = None      # Per-user mean rating (for normalization)
        self.predicted = None       # Full reconstructed rating matrix

    def fit(self, ratings_df: pd.DataFrame):
        """
        Train SVD on user-song ratings.
        ratings_df must have columns: user_id, song_id, rating
        """
        # Build index maps
        users = ratings_df["user_id"].unique()
        songs = ratings_df["song_id"].unique()
        self.user_index = {u: i for i, u in enumerate(users)}
        self.song_index = {s: i for i, s in enumerate(songs)}
        self.song_ids = list(songs)

        n_users, n_songs = len(users), len(songs)

        # Build rating matrix (users x songs), fill missing with 0
        R = np.zeros((n_users, n_songs))
        for _, row in ratings_df.iterrows():
            u = self.user_index[row["user_id"]]
            s = self.song_index[row["song_id"]]
            R[u, s] = row["rating"]

        # Normalize: subtract each user's mean rating (only for rated items)
        self.user_means = np.zeros(n_users)
        for u in range(n_users):
            rated = R[u, R[u] != 0]
            if len(rated) > 0:
                self.user_means[u] = rated.mean()
                R[u, R[u] != 0] -= self.user_means[u]

        # Truncated SVD
        print(f"Running SVD with {self.n_factors} latent factors on {n_users}x{n_songs} matrix...")
        U, sigma, Vt = np.linalg.svd(R, full_matrices=False)

        # Keep only top n_factors
        k = min(self.n_factors, len(sigma))
        self.user_factors = U[:, :k]
        self.sigma = sigma[:k]
        self.song_factors = Vt[:k, :]

        # Reconstruct full predicted rating matrix
        self.predicted = self.user_factors @ np.diag(self.sigma) @ self.song_factors

        # Add user means back
        self.predicted += self.user_means[:, np.newaxis]
        self.predicted = np.clip(self.predicted, 1, 5)

        # Evaluate on known ratings
        errors = []
        for _, row in ratings_df.iterrows():
            u = self.user_index[row["user_id"]]
            s = self.song_index[row["song_id"]]
            errors.append((self.predicted[u, s] - row["rating"]) ** 2)
        rmse = np.sqrt(np.mean(errors))
        print(f"✅ CollaborativeFilter: RMSE = {rmse:.4f} (numpy SVD, {k} factors)")
        return self

    def recommend(self, user_id: str, heard_song_ids: list, n: int = 10) -> list:
        """
        Returns top-N (song_id, predicted_rating) tuples for a user.
        Falls back to global song popularity order if user is unknown.
        """
        heard = set(heard_song_ids)

        if user_id not in self.user_index:
            # Unknown user — return songs not yet heard, ranked by avg predicted rating
            avg_ratings = self.predicted.mean(axis=0)
            ranked = np.argsort(avg_ratings)[::-1]
            return [
                (self.song_ids[i], float(avg_ratings[i]))
                for i in ranked
                if self.song_ids[i] not in heard
            ][:n]

        u = self.user_index[user_id]
        scores = self.predicted[u]
        ranked = np.argsort(scores)[::-1]
        return [
            (self.song_ids[i], float(scores[i]))
            for i in ranked
            if self.song_ids[i] not in heard
        ][:n]

    def predict_rating(self, user_id: str, song_id: str) -> float:
        if user_id not in self.user_index or song_id not in self.song_index:
            return 3.0  # Default fallback
        u = self.user_index[user_id]
        s = self.song_index[song_id]
        return float(self.predicted[u, s])

    def save(self, path="models/cf_model.pkl"):
        os.makedirs("models", exist_ok=True)
        joblib.dump(self, path)
        print(f"✅ Collaborative model saved to {path}")

    @classmethod
    def load(cls, path="models/cf_model.pkl"):
        return joblib.load(path)


if __name__ == "__main__":
    if not os.path.exists("data/user_ratings.csv"):
        print("No ratings found. Run ml/preprocessor.py first to generate mock ratings.")
    else:
        ratings_df = pd.read_csv("data/user_ratings.csv")
        model = CollaborativeRecommender().fit(ratings_df)
        model.save()

        sample_user = ratings_df["user_id"].iloc[0]
        heard = ratings_df[ratings_df["user_id"] == sample_user]["song_id"].tolist()
        recs = model.recommend(sample_user, heard, n=5)
        print(f"\nTop 5 predictions for {sample_user}:")
        for sid, score in recs:
            print(f"  {sid[:20]}... predicted rating: {score:.2f}")