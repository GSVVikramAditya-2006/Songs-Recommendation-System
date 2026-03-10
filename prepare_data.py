import pandas as pd
import numpy as np
import os

# Update this path if your downloaded file is somewhere else
df = pd.read_csv("dataset.csv")

print("Columns found:", df.columns.tolist())
print(f"Rows: {len(df)}")

df = df.rename(columns={
    "track_id": "id",
    "track_name": "title",
    "artists": "artist",
    "album_name": "album"
})

df = df.dropna(subset=["id", "title", "artist", "danceability", "energy"])
df = df.drop_duplicates(subset=["id"])

df["album_cover"] = ""
df["preview_url"] = ""
if "popularity" not in df.columns:
    df["popularity"] = 50

df["tempo_normalized"] = ((df["tempo"] - 60) / 140).clip(0, 1)
df["loudness_normalized"] = ((df["loudness"] + 60) / 60).clip(0, 1)

os.makedirs("data/processed", exist_ok=True)
df.to_csv("data/processed/songs_features.csv", index=False)
print(f"✅ Saved {len(df)} songs to data/processed/songs_features.csv")

# Keep only music (filter out podcasts/comedy/audiobooks by speechiness)
df = df[df["speechiness"] < 0.5]
# Keep only reasonably popular songs
df = df[df["popularity"] > 20]
print(f"After filtering: {len(df)} songs")