const FEATURE_LABELS = {
  danceability: "Dance",
  energy: "Energy",
  valence: "Mood",
  tempo_normalized: "Tempo",
  acousticness: "Acoustic",
  instrumentalness: "Instrumental",
};

const FEATURE_COLORS = {
  danceability: "#c9a84c",
  energy: "#f97316",
  valence: "#34d399",
  tempo_normalized: "#f472b6",
  acousticness: "#60a5fa",
  instrumentalness: "#a78bfa",
};

export function RadarChart({ features, size = 160 }) {
  const cx = size / 2, cy = size / 2, r = size * 0.36;
  const keys = Object.keys(FEATURE_LABELS).filter((k) => features[k] !== undefined);
  const n = keys.length;
  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2;
  const point = (i, val) => ({
    x: cx + r * val * Math.cos(angle(i)),
    y: cy + r * val * Math.sin(angle(i)),
  });
  const gridLevels = [0.25, 0.5, 0.75, 1.0];
  const gridPolygon = (level) =>
    keys.map((_, i) => { const p = point(i, level); return `${p.x},${p.y}`; }).join(" ");
  const dataPoints = keys.map((k, i) => point(i, features[k] || 0));
  const dataPolygon = dataPoints.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <svg width={size} height={size} style={{ overflow: "visible" }}>
      {gridLevels.map((lvl) => (
        <polygon key={lvl} points={gridPolygon(lvl)} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
      ))}
      {keys.map((_, i) => {
        const outer = point(i, 1);
        return <line key={i} x1={cx} y1={cy} x2={outer.x} y2={outer.y} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />;
      })}
      <polygon points={dataPolygon} fill="rgba(201,168,76,0.15)" stroke="#c9a84c" strokeWidth="1.5" />
      {dataPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={3} fill={FEATURE_COLORS[keys[i]]} />
      ))}
      {keys.map((k, i) => {
        const lp = point(i, 1.28);
        return (
          <text key={k} x={lp.x} y={lp.y} textAnchor="middle" dominantBaseline="middle"
            fontSize="7.5" fill="rgba(255,255,255,0.4)" fontFamily="'DM Sans', sans-serif">
            {FEATURE_LABELS[k]}
          </text>
        );
      })}
    </svg>
  );
}

export function FeatureBar({ label, value, color }) {
  return (
    <div style={{ marginBottom: 9 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
        <span style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", fontFamily: "'DM Sans', sans-serif" }}>{label}</span>
        <span style={{ fontSize: 10, color, fontFamily: "monospace" }}>{Math.round(value * 100)}</span>
      </div>
      <div style={{ height: 3, background: "rgba(255,255,255,0.07)", borderRadius: 2 }}>
        <div style={{ height: "100%", width: `${value * 100}%`, background: color, borderRadius: 2, transition: "width 0.7s cubic-bezier(0.4,0,0.2,1)" }} />
      </div>
    </div>
  );
}

export { FEATURE_LABELS, FEATURE_COLORS };
