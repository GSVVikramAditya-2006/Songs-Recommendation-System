"""
data_collector.py
-----------------
Fetches songs and their audio features from the Spotify API.
Saves raw data to data/raw/songs.json and processed features to data/processed/songs_features.csv

HOW TO USE:
  1. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env file
  2. Run: python ml/data_collector.py
"""

import os
import json
import time
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

PLAYLISTS = [
    "37i9dQZEVXbMDoHDwVN2tF",  # Top 50 Global
    "37i9dQZEVXbLiRSasKsNU9",  # Pop Rising
    "37i9dQZF1DX0XUsuxWHRQd",  # RapCaviar
    "37i9dQZF1DX4SBhb3fqCJd",  # Are & Be (R&B)
    "37i9dQZF1DXcBWIGoYBM5M",  # Today's Top Hits
]

AUDIO_FEATURE_KEYS = [
    "danceability", "energy", "valence", "tempo",
    "acousticness", "instrumentalness", "liveness", "speechiness", "loudness"
]


def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    ))


def fetch_tracks_from_playlist(sp, playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id, limit=50)
    for item in results["items"]:
        track = item.get("track")
        if not track or not track.get("id"):
            continue
        tracks.append({
            "id": track["id"],
            "title": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "album_cover": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
            "duration_ms": track["duration_ms"],
            "popularity": track["popularity"],
            "preview_url": track.get("preview_url", ""),
        })
    return tracks


def fetch_audio_features(sp, track_ids):
    features = {}
    # Spotify API allows up to 100 IDs per request
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        results = sp.audio_features(batch)
        for r in results:
            if r:
                features[r["id"]] = {k: r[k] for k in AUDIO_FEATURE_KEYS}
        time.sleep(0.1)  # respect rate limits
    return features


def normalize_tempo(tempo):
    """Normalize tempo (BPM) to 0-1 range. Typical range: 60-200 BPM."""
    return min(max((tempo - 60) / 140, 0), 1)


def normalize_loudness(loudness):
    """Normalize loudness (dB) to 0-1 range. Typical range: -60 to 0 dB."""
    return min(max((loudness + 60) / 60, 0), 1)


def collect_data():
    print("🎵 Connecting to Spotify API...")
    sp = get_spotify_client()

    all_tracks = {}
    print(f"📥 Fetching tracks from {len(PLAYLISTS)} playlists...")
    for pid in PLAYLISTS:
        tracks = fetch_tracks_from_playlist(sp, pid)
        for t in tracks:
            all_tracks[t["id"]] = t
        print(f"  ✓ {len(tracks)} tracks from playlist {pid[:8]}...")
        time.sleep(0.2)

    track_ids = list(all_tracks.keys())
    print(f"\n🔬 Fetching audio features for {len(track_ids)} unique tracks...")
    features = fetch_audio_features(sp, track_ids)

    # Merge tracks with features
    songs = []
    for tid, track in all_tracks.items():
        if tid in features:
            f = features[tid]
            songs.append({
                **track,
                **f,
                "tempo_normalized": normalize_tempo(f["tempo"]),
                "loudness_normalized": normalize_loudness(f["loudness"]),
            })

    # Save raw
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/songs.json", "w") as fp:
        json.dump(songs, fp, indent=2)
    print(f"\n✅ Saved {len(songs)} songs to data/raw/songs.json")

    # Save processed CSV
    os.makedirs("data/processed", exist_ok=True)
    df = pd.DataFrame(songs)
    df.to_csv("data/processed/songs_features.csv", index=False)
    print(f"✅ Saved processed features to data/processed/songs_features.csv")
    return df


if __name__ == "__main__":
    collect_data()
