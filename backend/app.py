from flask import Flask, jsonify
from flask_cors import CORS
import base64
import os
from detection import process_image_for_surveillance

app = Flask(__name__)
CORS(app)

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images", "real")
_image_index = [0]

LOCATION_META = {
    "mumbai": {"name": "Mumbai Harbor", "coords": "18.9217° N, 72.8347° E", "zone": "Maharashtra Coast"},
    "chennai": {"name": "Chennai Port", "coords": "13.0827° N, 80.2707° E", "zone": "Tamil Nadu Coast"},
    "kochi": {"name": "Kochi Harbor", "coords": "9.9312° N, 76.2673° E", "zone": "Kerala Coast"},
    "vizag": {"name": "Visakhapatnam Port", "coords": "17.6868° N, 83.2185° E", "zone": "Andhra Pradesh Coast"},
    "goa": {"name": "Mormugao Port, Goa", "coords": "15.4089° N, 73.7975° E", "zone": "Goa Coast"},
}

def get_location_meta(filename):
    fname = os.path.basename(filename).lower()
    for key, meta in LOCATION_META.items():
        if key in fname:
            return meta
    return {"name": "Indian Coastal Waters", "coords": "Unknown", "zone": "EEZ Zone"}


@app.route("/process-image", methods=["GET"])
def process_image():
    images = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    if not images:
        return jsonify({"error": "No images found in images/real/"}), 404

    img_file = images[_image_index[0] % len(images)]
    _image_index[0] = (_image_index[0] + 1) % len(images)
    img_path = os.path.join(IMAGE_DIR, img_file)

    result = process_image_for_surveillance(img_path)

    with open(result["annotated_path"], "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    meta = get_location_meta(img_file)

    return jsonify({
        "image": img_b64,
        "detections": result["detections"],
        "stats": result["stats"],
        "location": meta,
        "image_file": img_file,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Maritime Surveillance AI"})


if __name__ == "__main__":
    app.run(debug=False, port=5050, host="0.0.0.0")
