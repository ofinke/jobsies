#!/bin/sh
set -e

if [ "$1" = "worker" ]; then
    exec celery -A jobsies.celery_app worker --loglevel=info --beat
elif [ "$1" = "app" ]; then
    exec uvicorn jobsies.fastapi_app:app --host 0.0.0.0 --port 8000
else
    echo "Usage: $0 {worker|app}"
    exit 1
fi