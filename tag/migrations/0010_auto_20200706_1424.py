# Generated by Django 3.0.6 on 2020-07-06 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tag', '0009_remove_callback_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='tid',
            field=models.PositiveIntegerField(unique=True, verbose_name='标签识别码'),
        ),
    ]