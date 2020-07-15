import os
import uuid

from django.db import models
from user.models import User


def get_image_upload_path(device, filename):
    user: User = device.belongs_to
    extension = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex[:8], extension)
    return os.path.join('user_{}/{}/{}'.format(str(user.id), 'images', filename))


class Device(models.Model):
    name = models.CharField(verbose_name='设备名', max_length=32, blank=True)
    location = models.CharField(verbose_name='位置', max_length=128, blank=True)
    belongs_to = models.ForeignKey(User, verbose_name='属于用户', null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(verbose_name='是否激活', default=False)
    created = models.DateTimeField(verbose_name='新建时间', auto_now_add=True)
    device_id = models.CharField(verbose_name='华为云设备ID', max_length=128, unique=True)

    map_picture = models.ImageField(verbose_name='地图', height_field='map_picture_h', width_field='map_picture_w', upload_to=get_image_upload_path, null=True, default=None)
    map_picture_w = models.PositiveIntegerField(verbose_name='地图宽度', default=0)
    map_picture_h = models.PositiveIntegerField(verbose_name='地图高度', default=0)

    def __str__(self):
        return '[{}]{}'.format(self.device_id, self.name)

    class Meta:
        ordering = ('name', '-id')
