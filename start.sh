#!/bin/bash
# Production startup script for Vaurioajoneuvo Price Scraper

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
elif [ -d "env" ]; then
    echo "🔧 Activating virtual environment..."
    source env/bin/activate
else
    echo "⚠️  No virtual environment found. Using system Python."
fi

# Check if gunicorn is available
if ! command -v gunicorn &> /dev/null; then
    echo "❌ Gunicorn not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Load environment variables
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  .env file not found. Using default settings."
fi

echo "🚀 Starting Valvur application..."

# Start the application with Gunicorn
exec gunicorn \
    --bind 0.0.0.0:5050 \
    --workers 2 \
    --timeout 120 \
    --keepalive 60 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    run:app
