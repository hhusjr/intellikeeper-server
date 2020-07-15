from rest_framework import serializers

from device.iot import check_base_online
from device.models import Device
from intellikeeper_api.shortcodes import INTELLIKEEPER_BASE_SHORT_CODES


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = (
            'id',
            'device_id',
            'name',
            'is_active',
            'location',
            'created',
            'map_picture',
            'map_picture_w',
            'map_picture_h'
        )
        read_only_fields = ('is_online', 'is_active')

    def validate_device_id(self, device_id):
        if device_id not in INTELLIKEEPER_BASE_SHORT_CODES:
            raise serializers.ValidationError('不存在该基站')
        device_id = INTELLIKEEPER_BASE_SHORT_CODES[device_id]

        try:
            Device.objects.get(device_id=device_id)
            raise serializers.ValidationError('该设备已注册')
        except Device.DoesNotExist:
            pass

        if check_base_online(device_id) is None:
            raise serializers.ValidationError('不存在该基站')

        return device_id


class FullDeviceSerializer(DeviceSerializer):
    is_online = serializers.SerializerMethodField(read_only=True)

    class Meta(DeviceSerializer.Meta):
        fields = DeviceSerializer.Meta.fields + (
            'is_online',
        )
        read_only_fields = DeviceSerializer.Meta.read_only_fields + (
            'is_online',
        )

    def get_is_online(self, device: Device):
        return check_base_online(device.device_id)
