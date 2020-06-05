from rest_framework import serializers
from device.models import Device

from device.services import handshake_with


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = (
            'id',
            'uid',
            'name',
            'is_active',
            'location',
            'created'
        )
        read_only_fields = ('is_online', 'is_active')

    def validate_uid(self, uid):
        if not handshake_with(uid):
                raise serializers.ValidationError('无法连接基站，请确保基站已经启动')

        return uid
