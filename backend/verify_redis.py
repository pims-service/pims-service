import os
import django
from django.conf import settings
from django.core.cache import cache

def verify_redis():
    print("Checking Django settings for Cache...")
    if not hasattr(settings, 'CACHES'):
        print("Error: CACHES not found in settings.")
        return

    if 'default' not in settings.CACHES:
        print("Error: 'default' cache not found in CACHES.")
        return

    backend = settings.CACHES['default']['BACKEND']
    print(f"Cache Backend: {backend}")
    
    if 'django_redis' not in backend:
        print("Warning: Backend is not django_redis.")

    print("\nAttempting to connect to Redis and set a key...")
    try:
        cache.set('test_key', 'Hello from Redis!', timeout=30)
        value = cache.get('test_key')
        if value == 'Hello from Redis!':
            print("Successfully set and retrieved value from Redis!")
        else:
            print(f"Error: Retrieved unexpected value: {value}")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        django.setup()
        verify_redis()
    except Exception as e:
        print(f"Failed to setup Django: {e}")
