# Generated migration to add fade_in_duration field

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('pads', '0002_remove_pad_channel'),
    ]

    operations = [
        migrations.AddField(
            model_name='pad',
            name='fade_in_duration',
            field=models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
