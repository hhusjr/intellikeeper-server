# Generated by Django 3.0.6 on 2020-05-11 10:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tag', '0003_auto_20200511_0902'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='创建时间'),
        ),
    ]
