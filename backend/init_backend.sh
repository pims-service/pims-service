#!/bin/bash

# Wait for database
echo "Waiting for postgres..."

# Use pg_isready if available, or just a simple sleep
# Since we have a healthcheck in docker-compose, this script is a secondary safety measure
until python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('db', 5432))" 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL started"

# Run migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Create superuser if environment variables are provided
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser \
        --no-input \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL"
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
