from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db, UserRating, ListeningHistory
from backend.schemas import (
    RecommendRequest, RecommendResponse, RatingRequest,
    SongBase, RecommendedSong, AudioFeatures
)

router = APIRouter(prefix="/recommend", tags=["recommendations"])

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

@router.post("", response_model=RecommendResponse)
def get_recommendations(req: RecommendRequest, db: Session = Depends(get_db)):
    model = get_hybrid_model()
    heard = []
    if req.user_id:
        heard_rows = db.query(ListeningHistory.song_id).filter(ListeningHistory.user_id == req.user_id).all()
        heard = [r.song_id for r in heard_rows]
    try:
        seed_row = model.get_song_info(req.song_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Song '{req.song_id}' not found")
    recs_df = model.recommend(song_id=req.song_id, user_id=req.user_id, heard_song_ids=heard, n=req.n)
    recommendations = []
    for _, row in recs_df.iterrows():
        rec = RecommendedSong(
            **row_to_song_base(row),
            content_score=float(row.get("content_score", 0)),
            cf_score=float(row.get("cf_score", 0)),
            hybrid_score=float(row.get("hybrid_score", 0)),
            features=AudioFeatures(**row_to_features(row)),
        )
        recommendations.append(rec)
    alpha = float(recs_df["alpha_used"].iloc[0]) if len(recs_df) > 0 else 1.0
    mode = "hybrid" if alpha < 1.0 else "content-based (cold start)"
    return RecommendResponse(
        seed_song=SongBase(**row_to_song_base(seed_row)),
        recommendations=recommendations,
        model_info={"mode": mode, "alpha": alpha, "content_weight": f"{alpha*100:.0f}%", "cf_weight": f"{(1-alpha)*100:.0f}%"},
    )

@router.post("/rate")
def rate_song(req: RatingRequest, db: Session = Depends(get_db)):
    existing = db.query(UserRating).filter(UserRating.user_id == req.user_id, UserRating.song_id == req.song_id).first()
    if existing:
        existing.rating = req.rating
    else:
        db.add(UserRating(user_id=req.user_id, song_id=req.song_id, rating=req.rating))
    history = db.query(ListeningHistory).filter(ListeningHistory.user_id == req.user_id, ListeningHistory.song_id == req.song_id).first()
    if history:
        history.play_count += 1
    else:
        db.add(ListeningHistory(user_id=req.user_id, song_id=req.song_id))
    db.commit()
    return {"status": "ok", "message": f"Rating {req.rating} saved"}

@router.get("/history/{user_id}")
def get_history(user_id: str, db: Session = Depends(get_db)):
    rows = db.query(ListeningHistory).filter(ListeningHistory.user_id == user_id).order_by(ListeningHistory.listened_at.desc()).limit(50).all()
    return {"user_id": user_id, "history": [{"song_id": r.song_id, "play_count": r.play_count} for r in rows]}
