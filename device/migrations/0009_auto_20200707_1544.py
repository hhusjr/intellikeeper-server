# Generated by Django 3.0.6 on 2020-07-07 15:44

import device.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0008_auto_20200707_0632'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='map_picture_h',
            field=models.PositiveIntegerField(default=0, verbose_name='地图高度'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='device',
            name='map_picture_path',
            field=models.ImageField(default=0, height_field='map_picture_h', upload_to=device.models.get_image_upload_path, verbose_name='地图', width_field='map_picture_h'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='device',
            name='map_picture_w',
            field=models.PositiveIntegerField(default=0, verbose_name='地图宽度'),
            preserve_default=False,
        ),
    ]
