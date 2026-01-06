#!/bin/bash
echo "Starting Dog Health AI Backend Server..."
echo ""
echo "Make sure you have:"
echo "1. Activated the virtual environment"
echo "2. Installed all dependencies (pip install -r requirements.txt)"
echo "3. Set up the .env file with database credentials"
echo ""
cd "$(dirname "$0")"
uvicorn main:app --reload --host 0.0.0.0 --port 8000


