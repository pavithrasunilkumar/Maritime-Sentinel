import { useState, useEffect, useRef } from "react";
import "./App.css";

const API_URL = "http://localhost:5050";
const REFRESH_MS = 3000;

const ALERT_CONFIG = {
  NORMAL:   { color: "#22c55e", bg: "rgba(34,197,94,0.12)",  border: "rgba(34,197,94,0.4)",  label: "NORMAL",     icon: "●" },
  HIGH:     { color: "#f97316", bg: "rgba(249,115,22,0.12)", border: "rgba(249,115,22,0.4)", label: "SUSPICIOUS", icon: "▲" },
  CRITICAL: { color: "#ef4444", bg: "rgba(239,68,68,0.12)",  border: "rgba(239,68,68,0.4)",  label: "CRITICAL",   icon: "■" },
};

const SHIP_ICONS = { Cargo: "🚢", Patrol: "⛵", Fishing: "🎣", default: "🚤" };

function useMaritimeData() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [fadeIn, setFadeIn]   = useState(false);

  useEffect(() => {
    let alive = true;
    const fetchData = async () => {
      try {
        const res  = await fetch(`${API_URL}/process-image`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (alive) {
          setFadeIn(false);
          setTimeout(() => {
            setData(json);
            setLoading(false);
            setError(null);
            setFadeIn(true);
          }, 150);
        }
      } catch (e) {
        if (alive) { setError(e.message); setLoading(false); }
      }
    };
    fetchData();
    const id = setInterval(fetchData, REFRESH_MS);
    return () => { alive = false; clearInterval(id); };
  }, []);

  return { data, loading, error, fadeIn };
}

function StatCard({ label, value, color, sub }) {
  return (
    <div className="stat-card" style={{ "--accent": color }}>
      <div className="stat-value" style={{ color }}>{value}</div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

function AlertBadge({ alert }) {
  const cfg = ALERT_CONFIG[alert] || ALERT_CONFIG.NORMAL;
  return (
    <span className="alert-badge"
      style={{ color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>
      {cfg.icon} {cfg.label}
    </span>
  );
}

function DetectionRow({ det, index }) {
  const cfg  = ALERT_CONFIG[det.alert] || ALERT_CONFIG.NORMAL;
  const icon = SHIP_ICONS[det.ship_type] || SHIP_ICONS.default;
  return (
    <div className="det-row" style={{ "--row-color": cfg.color, animationDelay: `${index * 60}ms` }}>
      <div className="det-row-left">
        <span className="det-icon">{icon}</span>
        <div className="det-info">
          <div className="det-name">
            {det.vessel_name !== "Unknown"
              ? det.vessel_name
              : `${det.ship_type} Vessel #${det.id}`}
          </div>
          <div className="det-meta">
            {det.ship_type} · {(det.confidence * 100).toFixed(0)}% conf
            {det.has_ais ? ` · MMSI: ${det.mmsi}` : " · No AIS Signal"}
          </div>
        </div>
      </div>
      <AlertBadge alert={det.alert} />
    </div>
  );
}

function PulsingDot({ color }) {
  return (
    <span className="pulse-dot" style={{ "--dot-color": color }}>
      <span className="pulse-ring" />
    </span>
  );
}

function Clock() {
  const [t, setT] = useState(new Date());
  useEffect(() => { const id = setInterval(() => setT(new Date()), 1000); return () => clearInterval(id); }, []);
  return <span>{t.toLocaleTimeString("en-IN", { hour12: false })}</span>;
}

export default function App() {
  const { data, loading, error, fadeIn } = useMaritimeData();

  const stats      = data?.stats       || {};
  const detections = data?.detections  || [];
  const location   = data?.location    || {};

  const criticalDets   = detections.filter(d => d.alert === "CRITICAL");
  const suspiciousDets = detections.filter(d => d.alert === "HIGH");
  const normalDets     = detections.filter(d => d.alert === "NORMAL");

  const threatLevel = criticalDets.length > 0 ? "HIGH"
    : suspiciousDets.length > 0 ? "ELEVATED" : "LOW";
  const threatColor = criticalDets.length > 0 ? "#ef4444"
    : suspiciousDets.length > 0 ? "#f97316" : "#22c55e";

  return (
    <div className="app">

      {/* ── HEADER ─────────────────────────────────────────────── */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">⚓</span>
            <div>
              <div className="logo-title">MARITIME SENTINEL</div>
              <div className="logo-sub">AI Coastal Surveillance · Indian Navy EEZ</div>
            </div>
          </div>
        </div>

        <div className="header-center">
          {location.name && (
            <div className="location-pill">
              <span className="loc-dot">▶</span>
              <span className="loc-name">{location.name}</span>
              <span className="loc-sep">·</span>
              <span className="loc-coords">{location.coords}</span>
            </div>
          )}
        </div>

        <div className="header-right">
          <div className="status-cluster">
            <PulsingDot color="#22c55e" />
            <span className="status-live">LIVE</span>
            <span className="status-time"><Clock /></span>
          </div>
          <div className="zone-badge">{location.zone || "EEZ Zone"}</div>
        </div>
      </header>

      {/* ── MAIN ───────────────────────────────────────────────── */}
      <main className="main">

        {/* Image Panel */}
        <section className="image-panel">
          <div className="image-header">
            <span className="img-label">📡 SATELLITE FEED</span>
            {data?.image_file && <span className="img-filename">{data.image_file}</span>}
            <span className="img-refresh">↻ 3s AUTO</span>
          </div>

          <div className="image-wrap" style={{ opacity: fadeIn ? 1 : 0.55, transition: "opacity 0.4s ease" }}>
            {loading && !data && (
              <div className="image-loading">
                <div className="loading-spinner" />
                <div className="loading-text">Initialising satellite feed…</div>
              </div>
            )}
            {error && (
              <div className="image-error">
                <div className="error-icon">⚠</div>
                <div>Backend offline — start Flask on port 5050</div>
                <code>cd backend &amp;&amp; python app.py</code>
              </div>
            )}
            {data && (
              <img src={`data:image/jpeg;base64,${data.image}`}
                   alt="Annotated satellite frame" className="sat-image" />
            )}
          </div>

          {/* Legend */}
          <div className="image-legend">
            {Object.entries(ALERT_CONFIG).map(([k, cfg]) => (
              <span key={k} className="legend-item" style={{ color: cfg.color }}>
                {cfg.icon} {cfg.label}
              </span>
            ))}
            <span className="legend-item" style={{ color: "#60a5fa" }}>▥ RESTRICTED ZONE</span>
          </div>
        </section>

        {/* Side Panel */}
        <aside className="side-panel">

          {/* Stats */}
          <div className="panel-section">
            <div className="section-title">
              <span>DETECTION SUMMARY</span>
              <span className="section-badge">LIVE</span>
            </div>
            <div className="stats-grid">
              <StatCard label="Total Vessels"  value={stats.total       ?? "–"} color="#94a3b8" />
              <StatCard label="AIS Matched"    value={stats.ais_matched ?? "–"} color="#22c55e" sub="Identified" />
              <StatCard label="Suspicious"     value={stats.suspicious  ?? "–"} color="#f97316" sub="No AIS" />
              <StatCard label="Critical Alert" value={stats.critical    ?? "–"} color="#ef4444" sub="Restricted" />
            </div>
          </div>

          {/* Threat bar */}
          {data && stats.total > 0 && (
            <div className="panel-section">
              <div className="section-title"><span>THREAT DISTRIBUTION</span></div>
              <div className="threat-bar">
                {normalDets.length     > 0 && <div className="threat-seg" style={{ flex: normalDets.length,     background: "#22c55e" }} />}
                {suspiciousDets.length > 0 && <div className="threat-seg" style={{ flex: suspiciousDets.length, background: "#f97316" }} />}
                {criticalDets.length   > 0 && <div className="threat-seg" style={{ flex: criticalDets.length,   background: "#ef4444" }} />}
              </div>
              <div className="threat-labels">
                <span style={{ color: "#22c55e" }}>{normalDets.length} Normal</span>
                <span style={{ color: "#f97316" }}>{suspiciousDets.length} Suspicious</span>
                <span style={{ color: "#ef4444" }}>{criticalDets.length} Critical</span>
              </div>
            </div>
          )}

          {/* Vessel list */}
          <div className="panel-section detections-section">
            <div className="section-title">
              <span>VESSEL REGISTRY</span>
              <span className="section-badge">{detections.length} TRACKED</span>
            </div>
            <div className="det-list">
              {detections.length === 0 && !loading && (
                <div className="det-empty">No vessels detected in current frame</div>
              )}
              {criticalDets.map((d, i)   => <DetectionRow key={d.id} det={d} index={i} />)}
              {suspiciousDets.map((d, i) => <DetectionRow key={d.id} det={d} index={criticalDets.length + i} />)}
              {normalDets.map((d, i)     => <DetectionRow key={d.id} det={d} index={criticalDets.length + suspiciousDets.length + i} />)}
            </div>
          </div>

          {/* System status */}
          <div className="panel-section">
            <div className="section-title"><span>SYSTEM STATUS</span></div>
            <div className="sys-status-grid">
              {[
                { label: "AIS Receiver",   color: "#22c55e", value: "ONLINE",  vc: "#22c55e" },
                { label: "AI Engine",      color: "#22c55e", value: "ACTIVE",  vc: "#22c55e" },
                { label: "Satellite Feed", color: "#22c55e", value: "LIVE",    vc: "#22c55e" },
                { label: "Threat Level",   color: threatColor, value: threatLevel, vc: threatColor },
              ].map(({ label, color, value, vc }) => (
                <div key={label} className="sys-item">
                  <PulsingDot color={color} />
                  <span className="sys-label">{label}</span>
                  <span className="sys-value" style={{ color: vc }}>{value}</span>
                </div>
              ))}
            </div>
          </div>

        </aside>
      </main>

      {/* ── FOOTER ─────────────────────────────────────────────── */}
      <footer className="footer">
        <span>© 2025 Indian Naval Research Initiative</span>
        <span>AI-Driven Satellite Image Intelligence for Coastal Surveillance</span>
        <span>Classification: RESTRICTED</span>
      </footer>
    </div>
  );
}
