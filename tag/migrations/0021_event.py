# Generated by Django 3.0.6 on 2020-07-08 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tag', '0020_auto_20200708_0749'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=32, verbose_name='事件名')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='发生时间')),
                ('caused_by', models.IntegerField(choices=[(0, '测试'), (1, '信号丢失'), (2, '标签被移'), (3, '标签被取下')], verbose_name='事件原因')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tag.Tag', verbose_name='标签')),
            ],
            options={
                'ordering': ('-created', '-id'),
            },
        ),
    ]
