# 🚢 Maritime Sentinel — AI Coastal Surveillance System  

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Backend-Flask-black?logo=flask)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)
![Vite](https://img.shields.io/badge/Build-Vite-646CFF?logo=vite)
![OpenCV](https://img.shields.io/badge/Computer%20Vision-OpenCV-green?logo=opencv)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🌊 Overview  

**Maritime Sentinel** is an AI-powered coastal surveillance system that processes satellite imagery to detect ships, match AIS signals, and identify potential maritime threats in real time.

It simulates a **defense-grade intelligent monitoring system**, combining:
- Computer Vision  
- Spatial Intelligence  
- Real-time Analytics Dashboard  

---

## ⚙️ Key Features  

- 🛰️ Satellite Image Processing  
- 🚢 Ship Detection using OpenCV  
- 📡 AIS Signal Matching (Simulated)  
- ⚠️ Multi-Level Threat Detection  
- 📊 Live Dashboard (React + Vite)  
- 🔁 Auto-refresh every 3 seconds  
- 🎯 Restricted Zone Monitoring  

---

## 🧱 Tech Stack  

| Layer | Technology |
|------|-----------|
| Frontend | React + Vite |
| Backend | Flask |
| AI/ML | OpenCV |
| Language | Python, JavaScript |

---

## 📁 Project Structure  
maritime-surveillance/
├── backend/
│ ├── app.py
│ ├── detection.py
│ ├── requirements.txt
│ └── images/
│ ├── real/
│ └── annotated/
└── frontend/
├── src/
│ ├── App.jsx
│ └── App.css


---

## 🚀 Setup Instructions  

### 🔧 Prerequisites  

- Python 3.10+  
- Node.js 18+  

---

### ▶️ Backend Setup  

```bash
cd backend
pip install -r requirements.txt
python app.py
├── index.html
└── vite.config.js

**cd frontend
npm install
npm run dev**


System Workflow

| Module           | Description                                             |
| ---------------- | ------------------------------------------------------- |
| Image Source     | 5 real harbor satellite images (cycled every 3 seconds) |
| Detection Engine | OpenCV segmentation + contour filtering                 |
| AIS Matching     | Distance-based matching with simulated AIS              |
| Classification   | Based on bounding-box area                              |
| Alert Logic      | Rule-based threat classification                        |
| Dashboard        | Real-time visualization using React                     |



📡 API
GET /process-image
{
  "image": "<base64 JPEG>",
  "detections": [
    {
      "id": 1,
      "ship_type": "Cargo",
      "alert": "HIGH",
      "has_ais": false,
      "mmsi": null,
      "vessel_name": null,
      "confidence": 0.87,
      "bbox": [x, y, w, h]
    }
  ],
  "stats": {
    "total": 5,
    "ais_matched": 3,
    "suspicious": 1,
    "critical": 1,
    "normal": 3
  },
  "location": {
    "name": "Mumbai Harbor",
    "coords": [19.0760, 72.8777],
    "zone": "restricted"
  },
  "image_file": "mumbai_harbor_1.jpg"
}

GET /health

System health check endpoint
🚨 Alert Levels
| Color     | Meaning                              |
| --------- | ------------------------------------ |
| 🟢 Green  | Normal (AIS present)                 |
| 🟠 Orange | Suspicious (No AIS detected)         |
| 🔴 Red    | Critical (Restricted zone violation) |

📊 Results
✔️ Real-time vessel detection pipeline
✔️ AIS-based anomaly identification
✔️ Restricted zone violation detection
✔️ Interactive surveillance dashboard
✔️ Modular full-stack architecture
📄 Documentation

📌 The project includes:

📘 Detailed Project Report
📑 Research Paper

Available inside the docs/ folder.

🔮 Future Enhancements
YOLOv8 integration for improved detection
Real satellite data integration
Live AIS API integration
Cloud deployment (AWS / GCP)
Deep learning-based vessel classification

👩‍💻 Author
Pavithra S

