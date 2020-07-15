from django.db import models

from device.models import Device
from tag.events import EVENTS
from user.models import User


class TagCategory(models.Model):
    device = models.ForeignKey(Device, verbose_name='关联基站', on_delete=models.CASCADE)

    name = models.CharField(verbose_name='标签分类名称', max_length=32)
    parent_category = models.ForeignKey('TagCategory', on_delete=models.SET_NULL, verbose_name='父级分类', null=True)
    created = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    color = models.CharField(verbose_name='颜色', max_length=32)


class Reader(models.Model):
    rid = models.PositiveIntegerField(verbose_name='阅读器识别码', unique=True)
    name = models.CharField(verbose_name='名称', unique=True, max_length=64)
    device = models.ForeignKey(Device, verbose_name='对应设备', on_delete=models.CASCADE)
    x = models.FloatField(verbose_name='横坐标')
    y = models.FloatField(verbose_name='纵坐标')
    location = models.CharField(verbose_name='位置标注', max_length=128, default='')


class Tag(models.Model):
    device = models.ForeignKey(Device, verbose_name='关联基站', on_delete=models.CASCADE)
    tid = models.PositiveIntegerField(verbose_name='标签识别码', unique=True)
    name = models.CharField(verbose_name='标签名称', max_length=32)
    is_active = models.BooleanField(verbose_name='是否激活', default=False)
    category = models.ForeignKey(TagCategory, verbose_name='标签分类', on_delete=models.SET_NULL, null=True, related_name='tags')
    created = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    move_detect_on = models.BooleanField(verbose_name='启用运动传感器', default=False)
    light_detect_on = models.BooleanField(verbose_name='启用光线传感器', default=True)
    mute_mode_on = models.BooleanField(verbose_name='静音模式', default=False)

    is_online = models.BooleanField(verbose_name='是否在线', default=False)


class TagTrack(models.Model):
    tag = models.ForeignKey(Tag, verbose_name='标签', on_delete=models.CASCADE)

    reader1 = models.ForeignKey(Reader, verbose_name='阅读器1', on_delete=models.SET_NULL, null=True, related_name='as_reader1')
    distance1 = models.FloatField(verbose_name='距离1')

    reader2 = models.ForeignKey(Reader, verbose_name='阅读器2', on_delete=models.SET_NULL, null=True, related_name='as_reader2')
    distance2 = models.FloatField(verbose_name='距离2')

    reader3 = models.ForeignKey(Reader, verbose_name='阅读器3', on_delete=models.SET_NULL, null=True, related_name='as_reader3')
    distance3 = models.FloatField(verbose_name='距离3')

    created = models.DateTimeField(verbose_name='记录时间') # 不用auto_now_add，cloud提供记录时间


class Trigger(models.Model):
    name = models.CharField(verbose_name='触发器名', max_length=32)
    is_active = models.BooleanField(verbose_name='是否激活', default=True)
    callback_url = models.TextField(verbose_name='回调URL')
    callback_protocol = models.CharField(verbose_name='回调协议', max_length=16)
    callback_params = models.TextField(verbose_name='回调参数')
    callback_headers = models.TextField(verbose_name='回调附加HTTP Header')
    callback_method = models.IntegerField(verbose_name='请求类型', choices=(
        (1, 'GET'),
        (2, 'POST'),
        (3, 'PUT')
    ))
    created = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    belongs_to = models.ForeignKey(User, verbose_name='创建者', on_delete=models.CASCADE)


class Callback(models.Model):
    scope = models.IntegerField(verbose_name='作用范围', choices=(
        (1, '全局（对某个用户而言）'),
        (2, '基站'),
        (3, 'TAG')
    ))
    target = models.IntegerField(verbose_name='作用目标')
    is_active = models.BooleanField(verbose_name='是否激活', default=True)
    trigger = models.ForeignKey(Trigger, verbose_name='触发器', on_delete=models.CASCADE)
    created = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


class Event(models.Model):
    name = models.CharField(verbose_name='事件名', max_length=32, blank=True)
    created = models.DateTimeField(verbose_name='发生时间', auto_now_add=True)
    caused_by = models.IntegerField(verbose_name='事件原因', choices=EVENTS.values())
    tag = models.ForeignKey(Tag, verbose_name='标签', on_delete=models.CASCADE)

    class Meta:
        ordering = ('-created', '-id')
