#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting server..."
exec gunicorn hotel_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-80} \
    --workers 3 \
    --threads 2 \
    --access-logfile - \
    --error-logfile -
