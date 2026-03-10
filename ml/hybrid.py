"""
hybrid.py
---------
Combines content-based and collaborative filtering into a hybrid recommender.

Strategy: Weighted linear combination
  hybrid_score = α * content_score + (1 - α) * cf_score

  α (alpha) is dynamic:
    - If we have user data  → α = 0.4  (trust CF more)
    - If no user data       → α = 1.0  (pure content-based, cold start)

This handles the "cold start" problem: new users with no history get
content-based recommendations, while returning users get personalized CF.
"""

import numpy as np
import pandas as pd
from typing import Optional
from ml.content_based import ContentBasedRecommender
from ml.collaborative import CollaborativeRecommender
from ml.preprocessor import load_songs, CONTENT_FEATURES


class HybridRecommender:
    def __init__(
        self,
        content_model: ContentBasedRecommender,
        cf_model: Optional[CollaborativeRecommender] = None,
        alpha: float = 0.5,
    ):
        """
        content_model : trained ContentBasedRecommender
        cf_model      : trained CollaborativeRecommender (optional)
        alpha         : weight for content score (0.0 to 1.0)
                        alpha=1.0 → pure content-based
                        alpha=0.0 → pure collaborative
        """
        self.content_model = content_model
        self.cf_model = cf_model
        self.alpha = alpha
        self.df = content_model.df  # Reference to full songs dataframe

    def recommend(
        self,
        song_id: str,
        user_id: Optional[str] = None,
        heard_song_ids: Optional[list] = None,
        n: int = 10,
    ) -> pd.DataFrame:
        """
        Returns top-N recommendations as a DataFrame.

        song_id          : seed song for content-based filtering
        user_id          : user identifier for collaborative filtering (optional)
        heard_song_ids   : songs to exclude from results
        n                : number of recommendations
        """
        heard = set(heard_song_ids or [song_id])
        fetch_n = n * 4  # Fetch more to allow for merging/filtering

        # --- Content-based scores ---
        cb_recs = self.content_model.recommend(song_id, n=fetch_n)
        cb_scores = dict(zip(cb_recs["id"], cb_recs["content_score"]))

        # --- Collaborative scores (if user exists and CF model available) ---
        cf_scores = {}
        effective_alpha = self.alpha

        if self.cf_model is not None and user_id is not None:
            try:
                cf_preds = self.cf_model.recommend(
                    user_id, list(heard), n=fetch_n
                )
                # Normalize CF predicted ratings to 0-1
                if cf_preds:
                    max_r = max(r for _, r in cf_preds)
                    min_r = min(r for _, r in cf_preds)
                    rng = max_r - min_r if max_r != min_r else 1
                    cf_scores = {sid: (r - min_r) / rng for sid, r in cf_preds}
            except Exception:
                # User not in training set → fall back to content-based
                effective_alpha = 1.0
        else:
            effective_alpha = 1.0  # Cold start: no user → pure content

        # --- Merge scores ---
        all_ids = set(cb_scores) | set(cf_scores)
        scored = []
        for sid in all_ids:
            if sid in heard:
                continue
            cs = cb_scores.get(sid, 0.0)
            fs = cf_scores.get(sid, 0.0)
            hybrid = effective_alpha * cs + (1 - effective_alpha) * fs
            scored.append((sid, cs, fs, hybrid))

        scored.sort(key=lambda x: x[3], reverse=True)
        top = scored[:n]

        # --- Build result DataFrame ---
        id_to_row = {row["id"]: row for _, row in self.df.iterrows()}
        results = []
        for sid, cs, fs, hs in top:
            if sid not in id_to_row:
                continue
            row = id_to_row[sid].to_dict()
            row["content_score"] = round(cs, 4)
            row["cf_score"] = round(fs, 4)
            row["hybrid_score"] = round(hs, 4)
            row["alpha_used"] = effective_alpha
            results.append(row)

        return pd.DataFrame(results)

    def get_song_info(self, song_id: str) -> dict:
        row = self.df[self.df["id"] == song_id]
        if row.empty:
            raise ValueError(f"Song '{song_id}' not found")
        return row.iloc[0].to_dict()

    def search_songs(self, query: str, limit: int = 10) -> pd.DataFrame:
        q = query.lower()
        mask = (
            self.df["title"].str.lower().str.contains(q, na=False) |
            self.df["artist"].str.lower().str.contains(q, na=False) |
            self.df["album"].str.lower().str.contains(q, na=False)
        )
        return self.df[mask].head(limit)


if __name__ == "__main__":
    import joblib
    content_model = ContentBasedRecommender.load("models/content_model.pkl")
    cf_model = CollaborativeRecommender.load("models/cf_model.pkl")

    hybrid = HybridRecommender(content_model, cf_model, alpha=0.5)

    sample_id = hybrid.df["id"].iloc[0]
    sample_title = hybrid.df["title"].iloc[0]

    print(f"\n🎵 Hybrid recommendations for: {sample_title}")
    recs = hybrid.recommend(sample_id, user_id="user_0001", n=5)
    for _, row in recs.iterrows():
        print(f"  {row['title']} — {row['artist']} | hybrid={row['hybrid_score']:.3f} (cb={row['content_score']:.3f}, cf={row['cf_score']:.3f})")
