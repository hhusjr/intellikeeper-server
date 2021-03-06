# Generated by Django 3.0.6 on 2020-07-08 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0014_auto_20200707_1825'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='device',
            options={'ordering': ('name', '-id')},
        ),
        migrations.RemoveField(
            model_name='device',
            name='uid',
        ),
        migrations.AlterField(
            model_name='device',
            name='device_id',
            field=models.CharField(max_length=128, unique=True, verbose_name='华为云设备ID'),
        ),
    ]
