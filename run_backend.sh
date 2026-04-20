#!/bin/bash
echo "=== Maritime Sentinel — Backend ==="
cd "$(dirname "$0")/backend"
echo "Starting Flask on http://localhost:5050 ..."
python app.py
