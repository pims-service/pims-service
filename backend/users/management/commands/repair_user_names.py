import re
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Repairs empty full_name fields by parsing usernames (e.g. sarah.kim -> Sarah Kim)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting User Name Repair Operation...'))
        
        users_to_fix = User.objects.filter(full_name='')
        count = 0

        for user in users_to_fix:
            # Skip superusers/admins if they don't follow the pattern or if we want to leave them
            if user.is_superuser:
                continue

            # Clean username: remove trailing numbers, replace separators with space
            clean_name = re.sub(r'\d+$', '', user.username) # Remove trailing numbers
            clean_name = clean_name.replace('.', ' ').replace('_', ' ')
            
            # Title case it (e.g. sarah kim -> Sarah Kim)
            formatted_name = clean_name.title()
            
            if formatted_name:
                user.full_name = formatted_name
                user.save(update_fields=['full_name'])
                count += 1
                self.stdout.write(f"Updated: {user.username} -> {formatted_name}")

        self.stdout.write(self.style.SUCCESS(f'Successfully repaired {count} user names.'))
