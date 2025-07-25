#!/bin/bash
# Production startup script for Vaurioajoneuvo Price Scraper

# Load environment variables
export $(grep -v '^#' .env | xargs)

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
