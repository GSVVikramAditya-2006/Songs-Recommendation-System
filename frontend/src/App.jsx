import { useState, useEffect } from "react";
import SongCard from "./components/SongCard";
import { RadarChart, FeatureBar, FEATURE_LABELS, FEATURE_COLORS } from "./components/AudioFeatures";
import { getAllSongs, searchSongs, getSong, getRecommendations, rateSong } from "./api/client";
import axios from "axios";

const USER_ID = "user_demo_001";
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Get recommendations based on average features of all liked songs
async function getRecsFromLikes(likedSongs, n = 10) {
  if (likedSongs.length === 0) return null;
  if (likedSongs.length === 1) {
    return getRecommendations(likedSongs[0].id, USER_ID, n);
  }
  // Average the audio features of all liked songs
  const featureKeys = ["danceability","energy","valence","tempo_normalized","acousticness","instrumentalness","liveness","speechiness","loudness_normalized"];
  const avg = {};
  featureKeys.forEach(k => {
    const vals = likedSongs.map(s => s.features?.[k] ?? 0);
    avg[k] = vals.reduce((a, b) => a + b, 0) / vals.length;
  });
  // Use the liked song most similar to the average as seed
  let bestSong = likedSongs[0];
  let bestDist = Infinity;
  likedSongs.forEach(s => {
    const dist = featureKeys.reduce((sum, k) => sum + Math.pow((s.features?.[k] ?? 0) - avg[k], 2), 0);
    if (dist < bestDist) { bestDist = dist; bestSong = s; }
  });
  return getRecommendations(bestSong.id, USER_ID, n);
}

function HeartButton({ isLiked, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: isLiked ? "rgba(239,68,68,0.15)" : "rgba(255,255,255,0.05)",
        border: isLiked ? "1px solid rgba(239,68,68,0.4)" : "1px solid rgba(255,255,255,0.1)",
        borderRadius: 8, width: 36, height: 36, cursor: "pointer",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 16, transition: "all 0.2s",
        color: isLiked ? "#ef4444" : "rgba(255,255,255,0.3)",
      }}
      onMouseEnter={e => { if (!isLiked) e.currentTarget.style.borderColor = "rgba(239,68,68,0.3)"; e.currentTarget.style.color = "#ef4444"; }}
      onMouseLeave={e => { if (!isLiked) { e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "rgba(255,255,255,0.3)"; } }}
    >
      {isLiked ? "♥" : "♡"}
    </button>
  );
}

function ModelBadge({ info }) {
  if (!info) return null;
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
      <span style={{ fontSize: 10, color: "rgba(201,168,76,0.7)", background: "rgba(201,168,76,0.08)", border: "1px solid rgba(201,168,76,0.2)", borderRadius: 20, padding: "3px 10px", fontFamily: "'DM Sans', sans-serif" }}>
        {info.mode}
      </span>
      <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", fontFamily: "monospace" }}>
        content {info.content_weight} · collab {info.cf_weight}
      </span>
    </div>
  );
}

export default function App() {
  const [songs, setSongs] = useState([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);
  const [rightTab, setRightTab] = useState("recs");
  const [loadingSongs, setLoadingSongs] = useState(true);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [error, setError] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [likedSongs, setLikedSongs] = useState([]);
  const [likeRecsMode, setLikeRecsMode] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [totalSongs, setTotalSongs] = useState(0);
  const PAGE_SIZE = 100;

  // Load first page on mount
  useEffect(() => {
    getAllSongs(PAGE_SIZE, 0)
      .then(data => {
        setSongs(data.results);
        setTotalSongs(data.total);
        setHasMore(data.results.length === PAGE_SIZE);
        setOffset(PAGE_SIZE);
        setLoadingSongs(false);
      })
      .catch(() => { setError("Could not connect to API. Make sure the backend is running on port 8000."); setLoadingSongs(false); });
  }, []);

  // Load more when scrolled to bottom
  const handleLibraryScroll = async (e) => {
    if (loadingMore || !hasMore || searchResults) return;
    const el = e.target;
    if (el.scrollHeight - el.scrollTop - el.clientHeight < 100) {
      setLoadingMore(true);
      try {
        const data = await getAllSongs(PAGE_SIZE, offset);
        setSongs(prev => [...prev, ...data.results]);
        setOffset(prev => prev + PAGE_SIZE);
        setHasMore(data.results.length === PAGE_SIZE);
      } catch {}
      setLoadingMore(false);
    }
  };

  // Load song detail when selected
  useEffect(() => {
    if (!selected) return;
    getSong(selected.id)
      .then(setSelectedDetail)
      .catch(() => setSelectedDetail(null));
  }, [selected]);

  // Search
  useEffect(() => {
    if (!query.trim()) { setSearchResults(null); return; }
    const timer = setTimeout(() => {
      searchSongs(query, 30)
        .then(data => setSearchResults(data.results))
        .catch(() => setSearchResults([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (song) => {
    setSelected(song);
    setRecommendations([]);
    setModelInfo(null);
    setLikeRecsMode(false);
  };

  const handleToggleLike = async (song) => {
    const isLiked = likedSongs.some(s => s.id === song.id);
    if (isLiked) {
      setLikedSongs(prev => prev.filter(s => s.id !== song.id));
    } else {
      // Fetch features if not already loaded
      let songWithFeatures = song;
      if (!song.features) {
        try { songWithFeatures = await getSong(song.id); } catch {}
      }
      setLikedSongs(prev => [...prev, songWithFeatures]);
      // Submit rating 5 to backend
      try { await rateSong(USER_ID, song.id, 5); } catch {}
    }
  };

  const handleRecommend = async () => {
    if (!selected) return;
    setLoadingRecs(true);
    setRightTab("recs");
    setRecommendations([]);
    setModelInfo(null);
    setLikeRecsMode(false);
    try {
      const data = await getRecommendations(selected.id, USER_ID, 10);
      setRecommendations(data?.recommendations ?? []);
      setModelInfo(data?.model_info ?? null);
    } catch (err) {
      console.error("Recommendation error:", err);
      setRecommendations([]);
    } finally {
      setLoadingRecs(false);
    }
  };

  const handleRecsFromLikes = async () => {
    if (likedSongs.length === 0) return;
    setLoadingRecs(true);
    setRightTab("recs");
    setRecommendations([]);
    setModelInfo(null);
    setLikeRecsMode(true);
    try {
      const data = await getRecsFromLikes(likedSongs, 10);
      // Filter out already liked songs
      const likedIds = new Set(likedSongs.map(s => s.id));
      const filtered = (data?.recommendations ?? []).filter(r => !likedIds.has(r.id));
      setRecommendations(filtered);
      setModelInfo(data?.model_info ?? null);
    } catch (err) {
      console.error("Likes rec error:", err);
      setRecommendations([]);
    } finally {
      setLoadingRecs(false);
    }
  };

  const displayedSongs = searchResults !== null ? searchResults : songs;
  const features = selectedDetail?.features;

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; overflow: hidden; background: #08080f; }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-thumb { background: rgba(201,168,76,0.18); border-radius: 2px; }
        input:focus { outline: none; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes shimmer { 0%,100%{opacity:0.3} 50%{opacity:0.7} }
        @keyframes heartPop { 0%{transform:scale(1)} 50%{transform:scale(1.4)} 100%{transform:scale(1)} }
      `}</style>

      <div style={{ height: "100vh", background: "#08080f", color: "white", fontFamily: "'DM Sans', sans-serif", display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Header */}
        <header style={{ padding: "18px 28px", borderBottom: "1px solid rgba(255,255,255,0.045)", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 30, height: 30, borderRadius: 7, background: "linear-gradient(135deg, #c9a84c, #f97316)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15 }}>♪</div>
            <span style={{ fontFamily: "'Playfair Display', serif", fontSize: 19, fontWeight: 700, letterSpacing: "-0.3px" }}>Melodix</span>
            <span style={{ fontSize: 9, color: "rgba(255,255,255,0.2)", background: "rgba(255,255,255,0.04)", padding: "2px 6px", borderRadius: 4, marginLeft: 2, letterSpacing: "0.08em" }}>HYBRID ML</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {/* Likes counter in header */}
            {likedSongs.length > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "rgba(239,68,68,0.8)" }}>
                <span>♥</span>
                <span style={{ fontFamily: "monospace" }}>{likedSongs.length} liked</span>
              </div>
            )}
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.18)" }}>
              {songs.length > 0 ? `${songs.length} songs` : "connecting..."}
            </div>
          </div>
        </header>

        {error && (
          <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", margin: "12px 20px", borderRadius: 10, padding: "12px 16px", fontSize: 12, color: "rgba(239,68,68,0.9)" }}>
            {error}
          </div>
        )}

        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>

          {/* LEFT: Library */}
          <div style={{ width: 288, borderRight: "1px solid rgba(255,255,255,0.045)", display: "flex", flexDirection: "column", padding: "16px 14px" }}>
            <div style={{ marginBottom: 14, position: "relative" }}>
              <span style={{ position: "absolute", left: 11, top: "50%", transform: "translateY(-50%)", color: "rgba(255,255,255,0.2)", fontSize: 15, pointerEvents: "none" }}>⌕</span>
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search songs or artists..."
                style={{ width: "100%", background: "rgba(255,255,255,0.035)", border: "1px solid rgba(255,255,255,0.075)", borderRadius: 9, padding: "9px 11px 9px 30px", color: "white", fontSize: 12.5, fontFamily: "'DM Sans', sans-serif" }}
              />
              {query && <span onClick={() => setQuery("")} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: "rgba(255,255,255,0.25)", fontSize: 14 }}>×</span>}
            </div>

            <div style={{ fontSize: 9.5, color: "rgba(255,255,255,0.2)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 9, paddingLeft: 2 }}>
              {searchResults ? `${searchResults.length} results` : `Library · ${songs.length} / ${totalSongs}`}
            </div>

            <div onScroll={handleLibraryScroll} style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 5 }}>
              {loadingSongs ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} style={{ height: 66, borderRadius: 11, background: "rgba(255,255,255,0.025)", animation: "shimmer 1.5s infinite", animationDelay: `${i * 0.1}s` }} />
                ))
              ) : (
                displayedSongs.map((song, i) => (
                  <div key={song.id} style={{ animation: `fadeUp 0.25s ease ${Math.min(i, 10) * 0.03}s both`, position: "relative" }}>
                    <SongCard song={song} isSelected={selected?.id === song.id} onSelect={handleSelect} />
                    {/* Heart button overlaid on card */}
                    <div
                      onClick={(e) => { e.stopPropagation(); handleToggleLike(song); }}
                      style={{
                        position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)",
                        cursor: "pointer", fontSize: 14,
                        color: likedSongs.some(s => s.id === song.id) ? "#ef4444" : "rgba(255,255,255,0.15)",
                        transition: "all 0.2s",
                        animation: likedSongs.some(s => s.id === song.id) ? "heartPop 0.3s ease" : "none",
                      }}
                    >
                      {likedSongs.some(s => s.id === song.id) ? "♥" : "♡"}
                    </div>
                  </div>
                ))
              )}
              {loadingMore && (
                <div style={{ textAlign: 'center', padding: '12px 0', fontSize: 11, color: 'rgba(255,255,255,0.2)' }}>
                  Loading more songs...
                </div>
              )}
              {!hasMore && !searchResults && songs.length > 0 && (
                <div style={{ textAlign: 'center', padding: '10px 0', fontSize: 10, color: 'rgba(255,255,255,0.12)' }}>
                  All {totalSongs.toLocaleString()} songs loaded
                </div>
              )}
            </div>
          </div>

          {/* CENTER: Song Detail */}
          <div style={{ flex: 1, padding: "24px 28px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 22 }}>
            {!selected ? (
              <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 14, color: "rgba(255,255,255,0.12)" }}>
                <div style={{ fontSize: 48, animation: "shimmer 3s infinite" }}>♪</div>
                <div style={{ fontSize: 13 }}>Select a song from the library</div>
              </div>
            ) : (
              <>
                {/* Song Hero */}
                <div style={{ display: "flex", gap: 22, alignItems: "flex-start", animation: "fadeUp 0.3s ease" }}>
                  <div style={{
                    width: 96, height: 96, borderRadius: 14, flexShrink: 0,
                    background: selected.album_cover && selected.album_cover !== "nan"
                      ? `url(${selected.album_cover}) center/cover`
                      : `linear-gradient(135deg, hsl(${(selected.title?.charCodeAt(0)||0)*17%360},55%,25%), hsl(${(selected.title?.charCodeAt(0)||0)*17%360+60},45%,15%))`,
                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 38,
                    boxShadow: "0 16px 50px rgba(0,0,0,0.5)",
                  }}>
                    {(!selected.album_cover || selected.album_cover === "nan") && "♪"}
                  </div>
                  <div style={{ flex: 1 }}>
                    <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: 26, fontWeight: 700, lineHeight: 1.15, marginBottom: 6 }}>
                      {selected.title}
                    </h1>
                    <div style={{ fontSize: 14, color: "rgba(255,255,255,0.45)", marginBottom: 16 }}>
                      {selected.artist} · {selected.album}
                    </div>
                    <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                      {/* Like button */}
                      <HeartButton
                        isLiked={likedSongs.some(s => s.id === selected.id)}
                        onClick={() => handleToggleLike(selectedDetail || selected)}
                      />
                      {/* Recommend from this song */}
                      <button
                        onClick={handleRecommend}
                        disabled={loadingRecs}
                        style={{
                          background: loadingRecs ? "rgba(201,168,76,0.25)" : "linear-gradient(135deg, #c9a84c, #f97316)",
                          border: "none", borderRadius: 9, padding: "9px 20px",
                          color: loadingRecs ? "rgba(255,255,255,0.4)" : "#09090f",
                          fontFamily: "'DM Sans', sans-serif", fontWeight: 600, fontSize: 12.5,
                          cursor: loadingRecs ? "not-allowed" : "pointer",
                          display: "flex", alignItems: "center", gap: 7,
                        }}
                      >
                        {loadingRecs
                          ? <><span style={{ width: 11, height: 11, border: "2px solid rgba(255,255,255,0.25)", borderTopColor: "white", borderRadius: "50%", display: "inline-block", animation: "spin 0.7s linear infinite" }} />Analyzing...</>
                          : <>&#9670; Similar Songs</>
                        }
                      </button>
                    </div>
                  </div>
                </div>

                {/* Audio Features */}
                {features && (
                  <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.055)", borderRadius: 14, padding: "18px 22px", animation: "fadeUp 0.35s ease 0.05s both" }}>
                    <div style={{ fontSize: 10, color: "rgba(255,255,255,0.28)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 18 }}>Audio Features</div>
                    <div style={{ display: "flex", gap: 28, alignItems: "center" }}>
                      <RadarChart features={features} size={155} />
                      <div style={{ flex: 1 }}>
                        {Object.entries(FEATURE_LABELS).filter(([k]) => features[k] !== undefined).map(([k, label]) => (
                          <FeatureBar key={k} label={label} value={features[k]} color={FEATURE_COLORS[k]} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Liked Songs Panel */}
                {likedSongs.length > 0 && (
                  <div style={{ background: "rgba(239,68,68,0.04)", border: "1px solid rgba(239,68,68,0.12)", borderRadius: 14, padding: "16px 18px", animation: "fadeUp 0.35s ease 0.1s both" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                      <div style={{ fontSize: 10, color: "rgba(239,68,68,0.6)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
                        ♥ Liked Songs · {likedSongs.length}
                      </div>
                      <button
                        onClick={handleRecsFromLikes}
                        disabled={loadingRecs}
                        style={{
                          background: "linear-gradient(135deg, #ef4444, #f97316)",
                          border: "none", borderRadius: 8, padding: "7px 14px",
                          color: "#fff", fontFamily: "'DM Sans', sans-serif",
                          fontWeight: 600, fontSize: 11.5, cursor: loadingRecs ? "not-allowed" : "pointer",
                          display: "flex", alignItems: "center", gap: 6, opacity: loadingRecs ? 0.5 : 1,
                        }}
                      >
                        {loadingRecs ? "..." : <><span>♥</span> Recommend from Likes</>}
                      </button>
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {likedSongs.map(song => (
                        <div key={song.id} style={{
                          display: "flex", alignItems: "center", gap: 7,
                          background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
                          borderRadius: 20, padding: "4px 10px 4px 4px",
                        }}>
                          <div style={{ width: 22, height: 22, borderRadius: "50%", background: `linear-gradient(135deg, hsl(${(song.title?.charCodeAt(0)||0)*17%360},55%,30%), hsl(${(song.title?.charCodeAt(0)||0)*17%360+60},45%,20%))`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10 }}>♪</div>
                          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.7)", maxWidth: 100, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{song.title}</span>
                          <span
                            onClick={() => handleToggleLike(song)}
                            style={{ cursor: "pointer", color: "rgba(239,68,68,0.5)", fontSize: 12, marginLeft: 2 }}
                          >×</span>
                        </div>
                      ))}
                    </div>
                    <div style={{ marginTop: 10, fontSize: 10.5, color: "rgba(255,255,255,0.2)", fontStyle: "italic" }}>
                      Recommendations will blend audio features from all {likedSongs.length} liked songs
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* RIGHT: Recommendations */}
          <div style={{ width: 296, borderLeft: "1px solid rgba(255,255,255,0.045)", display: "flex", flexDirection: "column", padding: "16px 14px" }}>
            <div style={{ display: "flex", gap: 0, marginBottom: 16, background: "rgba(255,255,255,0.035)", borderRadius: 9, padding: 3 }}>
              {[["recs", "For You"], ["similar", "More Like This"]].map(([tab, label]) => (
                <button key={tab} onClick={() => setRightTab(tab)} style={{
                  flex: 1, padding: "7px 0", borderRadius: 7, border: "none", cursor: "pointer",
                  background: rightTab === tab ? "rgba(201,168,76,0.18)" : "transparent",
                  color: rightTab === tab ? "#c9a84c" : "rgba(255,255,255,0.28)",
                  fontSize: 11, fontWeight: 500, fontFamily: "'DM Sans', sans-serif", transition: "all 0.2s",
                }}>
                  {label}
                </button>
              ))}
            </div>

            {rightTab === "recs" ? (
              <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
                {modelInfo && <div style={{ marginBottom: 8 }}><ModelBadge info={modelInfo} /></div>}

                {likeRecsMode && recommendations.length > 0 && (
                  <div style={{ background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: 8, padding: "8px 12px", marginBottom: 6, fontSize: 10.5, color: "rgba(239,68,68,0.7)" }}>
                    ♥ Based on your {likedSongs.length} liked songs
                  </div>
                )}

                {recommendations.length === 0 && !loadingRecs ? (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "55%", gap: 12, color: "rgba(255,255,255,0.12)", textAlign: "center" }}>
                    <div style={{ fontSize: 36, animation: "shimmer 2.5s infinite" }}>♥</div>
                    <div style={{ fontSize: 12, lineHeight: 1.7 }}>
                      Like songs to get<br />
                      <span style={{ color: "rgba(239,68,68,0.45)" }}>personalised recommendations</span>
                      <br />or pick a song and tap<br />
                      <span style={{ color: "rgba(201,168,76,0.45)" }}>Similar Songs</span>
                    </div>
                  </div>
                ) : loadingRecs ? (
                  Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} style={{ height: 66, borderRadius: 11, background: "rgba(255,255,255,0.02)", animation: "shimmer 1.2s infinite", animationDelay: `${i*0.1}s` }} />
                  ))
                ) : (
                  <>
                    {recommendations.map((song, i) => (
                      <div key={song.id} style={{ animation: `fadeUp 0.35s ease ${i * 0.07}s both`, position: "relative" }}>
                        <SongCard song={song} isSelected={false} onSelect={handleSelect} score={song.hybrid_score} />
                        <div
                          onClick={() => handleToggleLike(song)}
                          style={{
                            position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)",
                            cursor: "pointer", fontSize: 13,
                            color: likedSongs.some(s => s.id === song.id) ? "#ef4444" : "rgba(255,255,255,0.15)",
                            transition: "color 0.2s",
                          }}
                        >
                          {likedSongs.some(s => s.id === song.id) ? "♥" : "♡"}
                        </div>
                      </div>
                    ))}
                    <div style={{ marginTop: 10, padding: "11px 13px", background: "rgba(255,255,255,0.015)", borderRadius: 9, fontSize: 10.5, color: "rgba(255,255,255,0.22)", lineHeight: 1.65 }}>
                      Like any of these to refine future recommendations.
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 5 }}>
                <div style={{ fontSize: 9.5, color: "rgba(255,255,255,0.18)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6, paddingLeft: 2 }}>More from library</div>
                {songs.filter(s => selected && s.artist === selected.artist && s.id !== selected.id).length > 0
                  ? songs.filter(s => selected && s.artist === selected.artist && s.id !== selected.id).map((song, i) => (
                    <div key={song.id} style={{ animation: `fadeUp 0.25s ease ${i * 0.04}s both` }}>
                      <SongCard song={song} isSelected={false} onSelect={handleSelect} />
                    </div>
                  ))
                  : songs.slice(0, 15).filter(s => s.id !== selected?.id).map((song, i) => (
                    <div key={song.id} style={{ animation: `fadeUp 0.25s ease ${i * 0.03}s both` }}>
                      <SongCard song={song} isSelected={false} onSelect={handleSelect} />
                    </div>
                  ))
                }
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}