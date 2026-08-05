#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Ensuring admin user exists..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@simplehotel.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"

echo "Starting server..."
exec gunicorn hotel_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-80} \
    --workers 3 \
    --threads 2 \
    --access-logfile - \
    --error-logfile -
