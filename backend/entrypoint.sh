#!/bin/sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Creating/updating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
import os
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@pims.local')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')

from users.models import Role
role, _ = Role.objects.get_or_create(name='Admin')

# Try to find the target user by new username first, then fall back to any existing superuser
u = None
if User.objects.filter(username=username).exists():
    u = User.objects.get(username=username)
    print(f'Superuser {username} already exists, updating credentials...')
else:
    # Check for the old default admin or any superuser to migrate
    for candidate_name in ['admin', 'administrator']:
        if User.objects.filter(username=candidate_name, is_superuser=True).exists():
            u = User.objects.get(username=candidate_name, is_superuser=True)
            print(f'Found existing superuser {candidate_name}, renaming to {username}...')
            break

if u is not None:
    u.username = username
    u.email = email
    u.set_password(password)
    u.role = role
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print(f'Superuser {username} credentials updated.')
else:
    u = User.objects.create_superuser(username=username, email=email, password=password)
    u.role = role
    u.save(update_fields=['role'])
    print(f'Superuser {username} created and assigned to Admin role.')
"

echo "Starting Daphne (ASGI server)..."
exec daphne -b 0.0.0.0 -p 8000 core.asgi:application
