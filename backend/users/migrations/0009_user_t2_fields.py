from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0008_rename_baseline_completed_at_user_onboarding_completed_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_completed_t2',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='t2_completed_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
