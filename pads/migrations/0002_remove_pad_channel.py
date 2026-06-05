# Generated migration to remove channel field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pads', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pad',
            name='channel',
        ),
    ]
