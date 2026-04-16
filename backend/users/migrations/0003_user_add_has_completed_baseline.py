from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_role_rename_registration_date_user_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_completed_baseline',
            field=models.BooleanField(default=False),
        ),
    ]
