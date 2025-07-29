#!/bin/bash
cd /home/valvur/app
source .venv/bin/activate
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
exec gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 2 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    run:app
