# Generated by Django 3.0.6 on 2020-07-08 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tag', '0019_reader_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reader',
            name='location',
            field=models.CharField(default='', max_length=128, verbose_name='位置标注'),
        ),
    ]