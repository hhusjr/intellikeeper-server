from rest_framework import serializers

from tag.models import Tag, Trigger


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'device',
            'tid',
            'name',
            'created',
            'is_active'
        )
        read_only_fields = (
            'tid',
        )

    def validate_device(self, device):
        if device.belongs_to != self.context['request'].user:
            raise serializers.ValidationError('基站设备不存在，或不属于你。')

        return device


class TriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trigger
        fields = (
            'id',
            'name',
            'is_active',
            'callback_url',
            'callback_method',
            'callback_protocol',
            'callback_params',
            'callback_headers',
            'created',
            'belongs_to'
        )
        read_only_fields = ('belongs_to', )
