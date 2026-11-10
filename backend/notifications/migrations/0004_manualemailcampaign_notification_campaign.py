import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_alter_notification_n_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ManualEmailCampaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('segment', models.CharField(choices=[('not_started', 'Not started'), ('stopped', 'Stopped'), ('d7_due', '7-day due'), ('all_eligible', 'All eligible'), ('manual', 'Picked by hand'), ('test', 'Test to admin')], max_length=20)),
                ('subject', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('recipient_count', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('queued', 'Queued'), ('sending', 'Sending'), ('done', 'Done')], default='queued', max_length=10)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manual_email_campaigns', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='notification',
            name='campaign',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='notifications.manualemailcampaign'),
        ),
    ]
