#!/bin/bash

echo "========================================"
echo "  AI Tester Framework v3.0 - Web UI"
echo "========================================"
echo ""
echo "Starting backend and frontend servers..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Start backend server
echo "[1/2] Starting FastAPI backend on port 8000..."
cd src/ai_tester/api
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ../../..

# Wait for backend to start
sleep 5

# Start frontend server
echo "[2/2] Starting React frontend on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "  Servers running!"
echo "========================================"
echo ""
echo "Backend API:  http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo "Frontend UI:  http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop servers"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
