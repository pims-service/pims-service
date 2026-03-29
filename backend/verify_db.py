import os
import django
from django.db import connections
from django.db.utils import OperationalError

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def verify_postgres_connection():
    print("Checking database connection...")
    db_conn = connections['default']
    try:
        # Try to obtain a cursor to verify the connection is alive
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✅ Successfully connected to PostgreSQL!")
                
                # Check for existing tables (to verify migrations)
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user_count = User.objects.count()
                print(f"✅ Django can read from the User table. Current users: {user_count}")
                
            else:
                print("❌ Unexpected result from SELECT 1")
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    verify_postgres_connection()
