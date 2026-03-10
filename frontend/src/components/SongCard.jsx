export default function SongCard({ song, isSelected, onSelect, score, rank }) {
  const hue = (song.title?.charCodeAt(0) || 0) * 17 % 360;

  return (
    <div
      onClick={() => onSelect(song)}
      style={{
        background: isSelected
          ? "linear-gradient(135deg, rgba(201,168,76,0.12), rgba(201,168,76,0.04))"
          : "rgba(255,255,255,0.025)",
        border: isSelected ? "1px solid rgba(201,168,76,0.35)" : "1px solid rgba(255,255,255,0.055)",
        borderRadius: 11,
        padding: "12px 14px",
        cursor: "pointer",
        transition: "all 0.18s ease",
        position: "relative",
        overflow: "hidden",
      }}
      onMouseEnter={(e) => { if (!isSelected) { e.currentTarget.style.background = "rgba(255,255,255,0.045)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; } }}
      onMouseLeave={(e) => { if (!isSelected) { e.currentTarget.style.background = "rgba(255,255,255,0.025)"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.055)"; } }}
    >
      {isSelected && (
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 3, background: "linear-gradient(180deg, #c9a84c, #f97316)", borderRadius: "11px 0 0 11px" }} />
      )}
      {score !== undefined && (
        <div style={{ position: "absolute", top: 9, right: 10, background: "rgba(201,168,76,0.12)", border: "1px solid rgba(201,168,76,0.25)", borderRadius: 20, padding: "2px 7px", fontSize: 9.5, color: "#c9a84c", fontFamily: "'DM Sans', sans-serif", letterSpacing: "0.02em" }}>
          {Math.round(score * 100)}%
        </div>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
        <div style={{
          width: 42, height: 42, borderRadius: 8, flexShrink: 0,
          background: song.album_cover
            ? `url(${song.album_cover}) center/cover`
            : `linear-gradient(135deg, hsl(${hue},55%,22%), hsl(${hue + 60},45%,14%))`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18,
        }}>
          {!song.album_cover && "♪"}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontFamily: "'Playfair Display', serif", fontSize: 13.5,
            color: isSelected ? "#c9a84c" : "rgba(255,255,255,0.88)",
            fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
          }}>
            {song.title}
          </div>
          <div style={{ fontSize: 11.5, color: "rgba(255,255,255,0.38)", fontFamily: "'DM Sans', sans-serif", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {song.artist}
          </div>
        </div>
      </div>
    </div>
  );
}
