# Generated by Django 3.0.6 on 2020-07-06 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0005_remove_device_is_online'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='uid',
            field=models.PositiveIntegerField(unique=True, verbose_name='识别码'),
        ),
    ]