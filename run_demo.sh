#!/bin/bash
set -e

echo "Killing any running python processes..."
pkill -f ats_oss.main || true

echo "Clearing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -r {} +

echo "Starting ATS-OSS server in the background..."
python -m ats_oss.main &
SERVER_PID=$!

# Wait for 10 seconds to ensure the server is fully initialized
echo "Waiting for server to start (PID: $SERVER_PID)..."
sleep 10

echo "Running the test submission script..."
python temp_test.py

echo "Shutting down the server..."
kill $SERVER_PID
# Wait for the process to be killed to avoid it becoming a zombie
wait $SERVER_PID || echo "Server process was already gone."

echo "Demo script finished."
