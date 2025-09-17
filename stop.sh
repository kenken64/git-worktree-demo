#!/bin/bash

# Find and kill Flask app process running on port 5001
echo "Stopping Flask app on port 5001..."

# Find process using port 5001
PID=$(lsof -ti:5001)

if [ -n "$PID" ]; then
    echo "Killing process $PID..."
    kill -TERM $PID
    sleep 2

    # Check if process is still running and force kill if necessary
    if kill -0 $PID 2>/dev/null; then
        echo "Process still running, force killing..."
        kill -KILL $PID
    fi

    echo "Flask app stopped successfully."
else
    echo "No process found running on port 5001."
fi