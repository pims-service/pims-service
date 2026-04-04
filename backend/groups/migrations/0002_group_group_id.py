from django.db import migrations, models


def seed_groups(apps, schema_editor):
    Group = apps.get_model('groups', 'Group')
    names = [
        'Group 1',
        'Group 2',
        'Group 3',
        'Group 4',
        'Group 5',
        'Group 6',
        'Group 7',
        'Group 8',
    ]
    for name in names:
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='id',
        ),
        migrations.AddField(
            model_name='group',
            name='group_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.RunPython(seed_groups, migrations.RunPython.noop),
    ]
