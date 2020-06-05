from django.db import models

from device.models import Device
from user.models import User


class Tag(models.Model):
    device = models.ForeignKey(Device, verbose_name='关联基站', on_delete=models.CASCADE)
    tid = models.CharField(verbose_name='标签识别码', max_length=32, unique=True)
    name = models.CharField(verbose_name='标签名称', max_length=32)
    is_active = models.BooleanField(verbose_name='是否激活', default=False)
    created = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)


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
