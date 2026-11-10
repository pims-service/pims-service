from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_passwordresetotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_consent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='email_unsubscribed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
