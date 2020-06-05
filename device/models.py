from user.models import User
from django.db import models


class Device(models.Model):
    uid = models.CharField(verbose_name='识别码', unique=True, max_length=16)
    name = models.CharField(verbose_name='设备名', max_length=32, blank=True)
    location = models.CharField(verbose_name='位置', max_length=128, blank=True)
    belongs_to = models.ForeignKey(User, verbose_name='属于用户', null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(verbose_name='是否激活', default=False)
    created = models.DateTimeField(verbose_name='新建时间', auto_now_add=True)

    def __str__(self):
        return '[{}]{}'.format(self.uid, self.name)

    class Meta:
        ordering = ('name', '-uid')
