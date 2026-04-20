# Maritime Sentinel — AI Coastal Surveillance System

AI-Driven Satellite Image Intelligence for Coastal Surveillance  
*College project · Indian Navy EEZ · Detection + AIS + Alerts*

---

## Folder Structure

```
maritime-surveillance/
├── backend/
│   ├── app.py            ← Flask API server
│   ├── detection.py      ← Ship detection + AIS matching + alerts
│   ├── requirements.txt
│   └── images/
│       ├── real/         ← Input satellite images (5 harbours)
│       └── annotated/    ← Auto-generated output frames
└── frontend/
    ├── src/
│   │   ├── App.jsx       ← Main dashboard component
│   │   └── App.css       ← Tactical dark UI design
    ├── index.html
    └── vite.config.js
```

---

## Setup Instructions

### 1 — Prerequisites
```bash
python 3.10+  (backend)
node  18+     (frontend)
```

### 2 — Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
# → running on http://localhost:5050
```

### 3 — Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
# → open http://localhost:5173
```

---

## How It Works

| Component | Logic |
|-----------|-------|
| **Image source** | 5 real coastal JPEG images in `images/real/`, cycled every 3 s |
| **Ship detection** | OpenCV colour-segmentation → contour filter (falls back from YOLO if weights absent) |
| **AIS matching** | Spatial distance match against 5 fixed virtual AIS transponders |
| **Classification** | Bounding-box area → Cargo / Patrol / Fishing |
| **Alert logic** | No AIS → HIGH · Right-side restricted zone → CRITICAL · else NORMAL |
| **Dashboard** | React (Vite) — live-refresh every 3 s, colour-coded detections |

---

## API

`GET /process-image`  
Returns JSON:
```json
{
  "image":      "<base64 JPEG>",
  "detections": [ { "id", "ship_type", "alert", "has_ais", "mmsi", "vessel_name", "confidence", "bbox" } ],
  "stats":      { "total", "ais_matched", "suspicious", "critical", "normal" },
  "location":   { "name", "coords", "zone" },
  "image_file": "mumbai_harbor_1.jpg"
}
```

`GET /health` — sanity check

---

## Alert Colour Codes

| Color  | Meaning |
|--------|---------|
| 🟢 Green  | NORMAL — AIS present, outside restricted zone |
| 🟠 Orange | HIGH — No AIS signal detected |
| 🔴 Red    | CRITICAL — Vessel in restricted zone |

