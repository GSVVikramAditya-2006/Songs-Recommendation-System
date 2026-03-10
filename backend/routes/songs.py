from fastapi import APIRouter, HTTPException, Query
from backend.schemas import SongDetail, SearchResponse, SongBase, AudioFeatures

router = APIRouter(prefix="/songs", tags=["songs"])

def get_hybrid_model():
    from backend.main import hybrid_model
    return hybrid_model

def row_to_song_base(row) -> dict:
    return {
        "id": str(row.get("id", "")),
        "title": str(row.get("title", "")),
        "artist": str(row.get("artist", "")),
        "album": str(row.get("album", "")),
        "album_cover": str(row.get("album_cover", "")),
        "preview_url": str(row.get("preview_url", "") or ""),
        "popularity": int(row.get("popularity", 0)),
    }

def row_to_features(row) -> dict:
    return {
        "danceability": float(row.get("danceability", 0)),
        "energy": float(row.get("energy", 0)),
        "valence": float(row.get("valence", 0)),
        "tempo_normalized": float(row.get("tempo_normalized", 0)),
        "acousticness": float(row.get("acousticness", 0)),
        "instrumentalness": float(row.get("instrumentalness", 0)),
        "liveness": float(row.get("liveness", 0)),
        "speechiness": float(row.get("speechiness", 0)),
        "loudness_normalized": float(row.get("loudness_normalized", 0)),
    }

@router.get("/search", response_model=SearchResponse)
def search_songs(q: str = Query(..., min_length=1), limit: int = Query(default=20, ge=1, le=100)):
    model = get_hybrid_model()
    results_df = model.search_songs(q, limit=limit)
    results = [SongBase(**row_to_song_base(row)) for _, row in results_df.iterrows()]
    return SearchResponse(results=results, total=len(results))

@router.get("/all", response_model=SearchResponse)
def get_all_songs(limit: int = Query(default=50, ge=1, le=100000), offset: int = Query(default=0, ge=0)):
    model = get_hybrid_model()
    df = model.df.iloc[offset:offset + limit]
    results = [SongBase(**row_to_song_base(row)) for _, row in df.iterrows()]
    return SearchResponse(results=results, total=len(model.df))

@router.get("/{song_id}", response_model=SongDetail)
def get_song(song_id: str):
    model = get_hybrid_model()
    try:
        row = model.get_song_info(song_id)
        return SongDetail(**row_to_song_base(row), features=AudioFeatures(**row_to_features(row)))
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Song '{song_id}' not found")
    