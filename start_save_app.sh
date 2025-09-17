#!/bin/bash

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

APP_NAME="save-app"
PID_FILE="$DIR/${APP_NAME}.pid"
LOG_DIR="$DIR/logs"
OUT_LOG="$LOG_DIR/${APP_NAME}.out"

mkdir -p "$LOG_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Prevent duplicate starts
if [[ -f "$PID_FILE" ]]; then
  if ps -p "$(cat "$PID_FILE")" > /dev/null 2>&1; then
    echo "$APP_NAME is already running with PID $(cat "$PID_FILE")"
    exit 0
  else
    echo "Found stale PID file; removing."
    rm -f "$PID_FILE"
  fi
fi

# Start the Flask save app in background
echo "Starting Flask save app on port 5001..."
nohup python save_app.py >> "$OUT_LOG" 2>&1 &
echo $! > "$PID_FILE"

echo "Started $APP_NAME (PID $(cat "$PID_FILE")). Logs: $OUT_LOG"