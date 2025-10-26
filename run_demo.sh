#!/bin/bash
set -e

echo "Starting ATS-OSS server in the background..."
python -m ats_oss.main &
SERVER_PID=$!

# Wait for 5 seconds to ensure the server is fully initialized
echo "Waiting for server to start (PID: $SERVER_PID)..."
sleep 5

echo "Running the demo submission script..."
python ats_oss/scripts/demo_submit.py

echo "Shutting down the server..."
kill $SERVER_PID
# Wait for the process to be killed to avoid it becoming a zombie
wait $SERVER_PID || echo "Server process was already gone."

echo "Demo script finished."
