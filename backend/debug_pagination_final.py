import os
import django
import json
from django.urls import reverse
from rest_framework.test import APIClient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
client = APIClient()
user = User.objects.filter(is_superuser=True).first()

if user:
    client.force_authenticate(user=user)
    response = client.get(reverse('admin_baseline_list'))
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        if isinstance(data, dict):
            print(f"Is paginated: True")
            print(f"Count: {data.get('count')}")
            print(f"Results length: {len(data.get('results', []))}")
        else:
            print(f"Is paginated: False")
            print(f"Data length: {len(data)}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw content: {response.content[:200]}")
else:
    print("No superuser found")
