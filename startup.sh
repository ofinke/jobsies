#!/bin/sh
set -e

# install plugin packages (if any)
if [ -n "${PLUGINS:-}" ]; then
    # Treat PLUGINS as a whitespace-separated list of package specs.
    set -f
    uv pip install --python /app/.venv/bin/python $PLUGINS 
fi

# Start the image as a setup job, worker, or application
if [ "$1" = "setup" ]; then
    exec python -m jobsies.database.setup
elif [ "$1" = "worker" ]; then
    exec celery -A jobsies.celery_app worker --loglevel=info --beat --scheduler redbeat.RedBeatScheduler
elif [ "$1" = "app" ]; then
    exec uvicorn jobsies.fastapi_app:app --host 0.0.0.0 --port 8000
else
    echo "Usage: $0 {setup|worker|app}"
    exit 1
fi
