# Generated by Django 3.0.6 on 2020-05-10 19:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('device', '0002_auto_20200510_1913'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='location',
            field=models.CharField(blank=True, max_length=128, verbose_name='位置'),
        ),
    ]
