"""
schemas.py
----------
Pydantic models for request/response validation in FastAPI.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AudioFeatures(BaseModel):
    danceability: float
    energy: float
    valence: float
    tempo_normalized: float
    acousticness: float
    instrumentalness: float
    liveness: float
    speechiness: float
    loudness_normalized: float


class SongBase(BaseModel):
    id: str
    title: str
    artist: str
    album: str
    album_cover: Optional[str] = ""
    preview_url: Optional[str] = ""
    popularity: Optional[int] = 0


class SongDetail(SongBase):
    features: AudioFeatures


class RecommendedSong(SongBase):
    content_score: float = 0.0
    cf_score: float = 0.0
    hybrid_score: float = 0.0
    features: Optional[AudioFeatures] = None


class RecommendRequest(BaseModel):
    song_id: str
    user_id: Optional[str] = None
    n: int = Field(default=10, ge=1, le=50)


class RecommendResponse(BaseModel):
    seed_song: SongBase
    recommendations: List[RecommendedSong]
    model_info: dict


class RatingRequest(BaseModel):
    user_id: str
    song_id: str
    rating: float = Field(ge=1.0, le=5.0)


class SearchResponse(BaseModel):
    results: List[SongBase]
    total: int
