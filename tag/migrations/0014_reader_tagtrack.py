# Generated by Django 3.0.6 on 2020-07-07 06:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0007_device_device_id'),
        ('tag', '0013_tagcategory_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reader',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rid', models.PositiveIntegerField(unique=True, verbose_name='阅读器识别码')),
                ('x', models.FloatField(verbose_name='横坐标')),
                ('y', models.FloatField(verbose_name='纵坐标')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='device.Device', verbose_name='对应设备')),
            ],
        ),
        migrations.CreateModel(
            name='TagTrack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distance1', models.FloatField(verbose_name='距离1')),
                ('distance2', models.FloatField(verbose_name='距离2')),
                ('distance3', models.FloatField(verbose_name='距离3')),
                ('created', models.DateTimeField(verbose_name='记录时间')),
                ('reader1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='as_reader1', to='tag.Reader', verbose_name='阅读器1')),
                ('reader2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='as_reader2', to='tag.Reader', verbose_name='阅读器2')),
                ('reader3', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='as_reader3', to='tag.Reader', verbose_name='阅读器3')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tag.Tag', verbose_name='标签')),
            ],
        ),
    ]
