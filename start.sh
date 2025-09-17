#!/usr/bin/env bash
# Start the Prompt Compressor web app as a background service.
# - Creates .venv if missing
# - Installs/updates deps with pip from requirements.txt
# - Loads .env
# - Uses .venv/bin/python
# - Writes logs to logs/prompt-compressor.out
# - Stores PID in prompt-compressor.pid

set -Eeuo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

APP_NAME="prompt-compressor"
PID_FILE="$DIR/${APP_NAME}.pid"
LOG_DIR="$DIR/logs"
OUT_LOG="$LOG_DIR/${APP_NAME}.out"

mkdir -p "$LOG_DIR"

# Load environment variables from .env if it exists
if [[ -f "$DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$DIR/.env"
  set +a
fi

# Ensure virtual environment exists
SYS_PY="${PYTHON:-python3}"
if [[ ! -x "$DIR/.venv/bin/python" ]]; then
  echo "Creating virtual environment at .venv ..."
  "$SYS_PY" -m venv "$DIR/.venv"
fi

VENV_PY="$DIR/.venv/bin/python"

# Ensure pip is available and up-to-date, then install dependencies
if ! "$VENV_PY" -m pip --version >/dev/null 2>&1; then
  "$VENV_PY" -m ensurepip --upgrade || true
fi
"$VENV_PY" -m pip install --upgrade pip
if [[ -f "$DIR/requirements.txt" ]]; then
  echo "Installing/updating dependencies from requirements.txt ..."
  "$VENV_PY" -m pip install -r "$DIR/requirements.txt"
fi

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

# Start command
# By default use `python app.py` per README. If you prefer Flask CLI, run with MODE=flask.
MODE="${MODE:-python}" # Accepts: python | flask

if [[ "$MODE" == "flask" ]]; then
  # Run Flask via module to ensure we use venv interpreter
  export FLASK_APP="app.py"
  export FLASK_ENV="${FLASK_ENV:-development}"
  export FLASK_RUN_HOST="${HOST:-127.0.0.1}"
  export FLASK_RUN_PORT="${PORT:-5000}"
  CMD=("$VENV_PY" -m flask run)
else
  CMD=("$VENV_PY" "$DIR/app.py")
fi

# Run in background
nohup "${CMD[@]}" >> "$OUT_LOG" 2>&1 &
echo $! > "$PID_FILE"

echo "Started $APP_NAME (PID $(cat "$PID_FILE")). Logs: $OUT_LOG"

