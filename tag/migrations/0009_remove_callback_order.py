# Generated by Django 3.0.6 on 2020-05-13 13:39

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('tag', '0008_trigger_belongs_to'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='callback',
            name='order',
        ),
    ]
