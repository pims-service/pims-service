from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0009_submission_entry_1_submission_entry_2_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='activity_wave',
            field=models.CharField(
                choices=[
                    ('PRE_T1', 'Pre T1'),
                    ('PRE_T2', 'Pre T2'),
                    ('PRE_T3', 'Pre T3'),
                    ('PRE_T4', 'Pre T4'),
                ],
                db_index=True,
                default='PRE_T1',
                max_length=10,
            ),
        ),
        migrations.RemoveConstraint(
            model_name='submission',
            name='unique_user_experiment_day',
        ),
        migrations.AddConstraint(
            model_name='submission',
            constraint=models.UniqueConstraint(
                fields=('user', 'activity_wave', 'experiment_day'),
                name='unique_user_wave_experiment_day',
            ),
        ),
    ]
