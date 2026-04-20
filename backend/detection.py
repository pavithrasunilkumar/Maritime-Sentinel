"""
detection.py  –  Maritime Sentinel
Ship detection tuned for realistic satellite/aerial imagery.
Pipeline: multi-channel segmentation → contour filter → AIS match → classify → alert
"""

import os, cv2, numpy as np, math, time

ANNOTATED_DIR = os.path.join(os.path.dirname(__file__), "images", "annotated")
os.makedirs(ANNOTATED_DIR, exist_ok=True)

# ── Virtual AIS transponder database (spatially fixed) ───────────────────────
AIS_DATABASE = [
    {"mmsi": "419001234", "vessel": "MV Ratnagiri",  "flag": "IN", "x": 0.36, "y": 0.58},
    {"mmsi": "419005678", "vessel": "INS Karwar",     "flag": "IN", "x": 0.51, "y": 0.65},
    {"mmsi": "419009012", "vessel": "MV Shalimar",   "flag": "IN", "x": 0.67, "y": 0.54},
    {"mmsi": "636012345", "vessel": "Silver Trader",  "flag": "LR", "x": 0.44, "y": 0.74},
    {"mmsi": "477654321", "vessel": "Ocean Pearl",    "flag": "HK", "x": 0.73, "y": 0.72},
]
MATCH_THRESH     = 0.20    # normalised distance for AIS match
RESTRICTED_X     = 0.72    # right-side restricted zone


def _norm_dist(cx, cy, W, H, ais):
    ax, ay = ais["x"] * W, ais["y"] * H
    return math.hypot(cx - ax, cy - ay) / max(W, H)


def _classify(w, h):
    area = w * h
    if area > 4500: return "Cargo"
    if area > 1800: return "Patrol"
    return "Fishing"


def _alert(has_ais, cx, W):
    if cx / W > RESTRICTED_X: return "CRITICAL"
    if not has_ais:            return "HIGH"
    return "NORMAL"


# ── Multi-strategy ship detector ─────────────────────────────────────────────
def _detect_ships(img_bgr, max_det=6, conf_thresh=0.38):
    H, W = img_bgr.shape[:2]
    water_top = H // 3          # sky / land is top-third
    roi = img_bgr[water_top:, :]

    gray   = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    hsv    = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    rH, W_ = roi.shape[:2]

    # Strategy 1: Bright objects against water
    water_hsv  = cv2.inRange(hsv, (85, 15, 25), (140, 255, 255))
    non_water  = cv2.bitwise_not(water_hsv)
    mean_g     = float(gray.mean())
    _, bright  = cv2.threshold(gray, int(mean_g + 12), 255, cv2.THRESH_BINARY)
    s1 = cv2.bitwise_and(bright, non_water)

    # Strategy 2: Local contrast — ships have strong edges in water
    laplacian  = cv2.Laplacian(gray, cv2.CV_32F)
    lap_abs    = np.abs(laplacian).astype(np.uint8)
    _, s2      = cv2.threshold(lap_abs, 18, 255, cv2.THRESH_BINARY)

    # Strategy 3: Saturation anomaly — metallic hulls less saturated than water
    sat        = hsv[:, :, 1]
    _, s3_lo   = cv2.threshold(sat, 60, 255, cv2.THRESH_BINARY_INV)  # low saturation
    s3         = cv2.bitwise_and(s3_lo, non_water)

    # Combine with voting
    combined   = cv2.bitwise_or(s1, cv2.bitwise_and(s2, s3))

    # Morphological clean-up
    k3  = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    k5  = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 5))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k3, iterations=3)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN,  k3, iterations=1)
    combined = cv2.dilate(combined, k5, iterations=1)

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    dets = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 250 or area > 80000:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        aspect = w / max(h, 1)
        if aspect < 0.6 or aspect > 16:
            continue
        # Confidence: blend of area score + contrast score
        region = gray[y:y+h, x:x+w]
        contrast_score = float(region.std()) / 60.0
        area_score     = min(1.0, area / 10000)
        score          = 0.4 + contrast_score * 0.35 + area_score * 0.25
        score          = min(0.97, score)
        if score < conf_thresh:
            continue
        # Offset y back to full image
        dets.append((x, y + water_top, x + w, y + water_top + h, round(score, 2)))

    # Sort largest first, deduplicate with NMS-style IoU check, keep top N
    dets.sort(key=lambda d: (d[2]-d[0])*(d[3]-d[1]), reverse=True)
    dets = _nms(dets, iou_thresh=0.35)
    return dets[:max_det]


def _nms(dets, iou_thresh=0.35):
    """Simple greedy NMS."""
    keep = []
    for d in dets:
        x1,y1,x2,y2,_ = d
        suppressed = False
        for k in keep:
            kx1,ky1,kx2,ky2,_ = k
            ix1,iy1 = max(x1,kx1), max(y1,ky1)
            ix2,iy2 = min(x2,kx2), min(y2,ky2)
            if ix2 > ix1 and iy2 > iy1:
                inter = (ix2-ix1)*(iy2-iy1)
                union = (x2-x1)*(y2-y1) + (kx2-kx1)*(ky2-ky1) - inter
                if union > 0 and inter/union > iou_thresh:
                    suppressed = True
                    break
        if not suppressed:
            keep.append(d)
    return keep


# ── YOLO fallback (if weights exist locally) ─────────────────────────────────
def _get_detections(img_bgr, max_det=6):
    try:
        from ultralytics import YOLO
        model_path = os.path.join(os.path.dirname(__file__), "yolov8n.pt")
        if not os.path.exists(model_path):
            raise FileNotFoundError
        model   = YOLO(model_path)
        results = model(img_bgr, conf=0.38, iou=0.40, verbose=False)[0]
        dets = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in (8, 7):
                continue
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            dets.append((x1,y1,x2,y2, round(float(box.conf[0]),2)))
        dets.sort(key=lambda d:(d[2]-d[0])*(d[3]-d[1]), reverse=True)
        return dets[:max_det]
    except Exception:
        return _detect_ships(img_bgr, max_det=max_det)


# ── Main entry point ─────────────────────────────────────────────────────────
def process_image_for_surveillance(img_path: str) -> dict:
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Cannot read image: {img_path}")
    H, W = img.shape[:2]

    raw = _get_detections(img)
    out = img.copy()

    # Restricted zone overlay
    rz_x = int(RESTRICTED_X * W)
    ov = out.copy()
    cv2.rectangle(ov, (rz_x, 0), (W, H), (0, 0, 160), -1)
    cv2.addWeighted(ov, 0.07, out, 0.93, 0, out)
    cv2.line(out, (rz_x, 0), (rz_x, H), (60, 60, 200), 1)
    _label_bg(out, "⚠ RESTRICTED ZONE", rz_x+5, 14, (80,80,220), fs=0.42)

    detections = []
    ais_count  = 0

    COLOR = {"NORMAL":(40,200,80), "HIGH":(30,150,255), "CRITICAL":(30,30,220)}

    for (x1,y1,x2,y2,score) in raw:
        cx, cy = (x1+x2)//2, (y1+y2)//2
        bw, bh = x2-x1, y2-y1

        # AIS match
        matched = None
        best_d  = float("inf")
        for ais in AIS_DATABASE:
            d = _norm_dist(cx, cy, W, H, ais)
            if d < best_d:
                best_d = d
                if d < MATCH_THRESH:
                    matched = ais
        has_ais = matched is not None
        if has_ais:
            ais_count += 1

        stype = _classify(bw, bh)
        alert = _alert(has_ais, cx, W)
        col   = COLOR[alert]

        # Draw box + corner accents
        cv2.rectangle(out, (x1,y1), (x2,y2), col, 2)
        _corners(out, x1,y1,x2,y2, col, min(bw,bh)//4, 3)

        # Label
        ais_tag = f"AIS·{matched['mmsi'][-4:]}" if has_ais else "NO AIS"
        lbl     = f"{stype}  {alert}  {ais_tag}"
        ly      = y1-6 if y1>20 else y2+16
        _label_bg(out, lbl, x1, ly, col, fs=0.42)

        # Confidence indicator dot
        cv2.circle(out, (x2-6, y1+6), 4, col, -1)

        detections.append({
            "id": len(detections)+1,
            "ship_type": stype, "alert": alert,
            "has_ais": has_ais,
            "mmsi": matched["mmsi"] if has_ais else None,
            "vessel_name": matched["vessel"] if has_ais else "Unknown",
            "confidence": score,
            "bbox": [x1,y1,x2,y2],
            "center": [cx,cy],
        })

    total     = len(detections)
    suspicious= sum(1 for d in detections if d["alert"]!="NORMAL")
    critical  = sum(1 for d in detections if d["alert"]=="CRITICAL")
    _stats_overlay(out, total, ais_count, suspicious, critical)

    out_name = f"ann_{int(time.time()*1000)}_{os.path.basename(img_path)}"
    out_path = os.path.join(ANNOTATED_DIR, out_name)
    cv2.imwrite(out_path, out, [cv2.IMWRITE_JPEG_QUALITY, 90])

    return {
        "annotated_path": out_path,
        "detections": detections,
        "stats": {
            "total": total, "ais_matched": ais_count,
            "suspicious": suspicious, "critical": critical,
            "normal": total-suspicious,
        },
    }


# ── Drawing helpers ───────────────────────────────────────────────────────────
def _label_bg(img, text, x, y, color, fs=0.42):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw,th),_ = cv2.getTextSize(text, font, fs, 1)
    p = 3
    cv2.rectangle(img, (x-p,y-th-p), (x+tw+p,y+p), (8,10,14), -1)
    cv2.rectangle(img, (x-p,y-th-p), (x+tw+p,y+p), color, 1)
    cv2.putText(img, text, (x,y), font, fs, color, 1, cv2.LINE_AA)

def _corners(img, x1,y1,x2,y2, color, L, thick):
    for (cx_,cy_), (hx,hy), (vx,vy) in [
        ((x1,y1),(x1+L,y1),(x1,y1+L)),
        ((x2,y1),(x2-L,y1),(x2,y1+L)),
        ((x1,y2),(x1+L,y2),(x1,y2-L)),
        ((x2,y2),(x2-L,y2),(x2,y2-L)),
    ]:
        cv2.line(img,(cx_,cy_),(hx,hy),color,thick)
        cv2.line(img,(cx_,cy_),(vx,vy),color,thick)

def _stats_overlay(img, total, ais, susp, crit):
    H,W = img.shape[:2]
    x0,y0,pw,ph = 8, H-78, 270, 72
    ov = img.copy()
    cv2.rectangle(ov,(x0,y0),(x0+pw,y0+ph),(8,10,14),-1)
    cv2.addWeighted(ov,0.72,img,0.28,0,img)
    cv2.rectangle(img,(x0,y0),(x0+pw,y0+ph),(45,50,60),1)
    f = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img,"SURVEILLANCE STATS",(x0+6,y0+14),f,0.38,(150,155,175),1)
    cv2.line(img,(x0+6,y0+18),(x0+pw-6,y0+18),(45,50,60),1)
    for i,(txt,col) in enumerate([
        (f"TOTAL VESSELS   {total}", (170,175,195)),
        (f"AIS MATCHED     {ais}",   (40,200,80)),
        (f"SUSPICIOUS      {susp}",  (30,150,255)),
        (f"CRITICAL        {crit}",  (80,80,220)),
    ]):
        cv2.putText(img,txt,(x0+6,y0+30+i*12),f,0.35,col,1)
