#!/bin/sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Creating superuser (if not exists)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
import os
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@pims.local')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created.')
else:
    print(f'Superuser {username} already exists.')
"

echo "Starting Gunicorn..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
