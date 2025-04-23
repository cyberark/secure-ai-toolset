#!/bin/bash

# =============================================================================
# Agent Guard Servers Launcher
# =============================================================================
# This script launches the Agent Guard Admin UI and API servers.
# - Admin UI: Streamlit interface running on port 8080
# - API Server: FastAPI application running on port 8081
#
# Usage: ./run_servers.sh
# =============================================================================

# Exit immediately if any command exits with non-zero status
set -e

# Activate the virtual environment
echo "Activating virtual environment..."
source ./.venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment. Make sure it exists at ./.venv/"
    exit 1
fi
echo "Virtual environment activated successfully."

# Function to cleanup processes on exit
cleanup() {
    echo -e "\nShutting down all servers..."
    # Kill all background processes
    kill $(jobs -p) 2>/dev/null || true
    wait
    echo "All servers have been stopped."
    exit 0
}

# Set up trap to catch termination signals
trap cleanup SIGINT SIGTERM EXIT

echo "Starting Agent Guard servers..."

# Start the Admin UI (Streamlit) server in background
echo "Launching Admin UI server on port 8080..."
python -m streamlit run servers/admin_ui/landing.py --server.port 8080 &
STREAMLIT_PID=$!

# Check if Streamlit started successfully
sleep 2
if ! ps -p $STREAMLIT_PID > /dev/null; then
    echo "ERROR: Failed to start Admin UI server"
    cleanup
fi

# Start the API server in background
echo "Launching API server on port 8081..."
python -m uvicorn servers.api_servers.main:app --host 0.0.0.0 --port 8081 &
API_PID=$!

# Check if API server started successfully
sleep 2
if ! ps -p $API_PID > /dev/null; then
    echo "ERROR: Failed to start API server"
    cleanup
fi

echo -e "\nAll servers are running!"
echo "Admin UI is available at http://localhost:8080"
echo "API Server is available at http://localhost:8081"
echo -e "\nPress any key to stop all servers..."

# Wait for a keypress
read -n 1

# cleanup function will be called automatically on exit

