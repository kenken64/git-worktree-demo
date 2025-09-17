#!/usr/bin/env bash
# Stop the Prompt Compressor web app using the recorded PID.

set -Eeuo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

APP_NAME="prompt-compressor"
PID_FILE="$DIR/${APP_NAME}.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No PID file found ($PID_FILE). Is $APP_NAME running?"
  exit 1
fi

PID="$(cat "$PID_FILE")"
if ! ps -p "$PID" > /dev/null 2>&1; then
  echo "Process $PID not running. Removing stale PID file."
  rm -f "$PID_FILE"
  exit 0
fi

echo "Stopping $APP_NAME (PID $PID) ..."
kill "$PID" || true

# Wait up to 10 seconds, then force kill
for i in {1..10}; do
  if ! ps -p "$PID" > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ps -p "$PID" > /dev/null 2>&1; then
  echo "Force killing $APP_NAME (PID $PID)"
  kill -9 "$PID" || true
fi

rm -f "$PID_FILE"
echo "Stopped $APP_NAME."

