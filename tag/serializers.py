import math
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from device.serializers import DeviceSerializer
from tag.models import Tag, Trigger, TagCategory, Reader, TagTrack, Event
from tag.facade import tag_get_path


class ReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reader
        fields = (
            'id',
            'rid',
            'name',
            'x',
            'y',
            'location'
        )
        read_only_fields = (
            'rid',
            'path'
        )


class TagSerializer(serializers.ModelSerializer):
    path = serializers.SerializerMethodField(read_only=True)
    color = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tag
        fields = (
            'id',
            'device',
            'tid',
            'name',
            'created',
            'is_active',
            'path',
            'category',
            'move_detect_on',
            'light_detect_on',
            'color',
            'is_online'
        )
        read_only_fields = (
            'tid',
            'path',
            'color'
        )

    def get_path(self, obj: Tag):
        return tag_get_path(obj)

    def get_color(self, obj: Tag):
        if obj.category is None:
            return '#000000'
        return obj.category.color

    def validate_device(self, device):
        if device.belongs_to != self.context['request'].user:
            raise serializers.ValidationError('基站设备不存在，或不属于你。')

        return device


class TrackedTagSerializer(TagSerializer):
    track = serializers.SerializerMethodField(read_only=True)

    class Meta(TagSerializer.Meta):
        fields = TagSerializer.Meta.fields + (
            'track',
        )
        read_only_fields = ('track', )

    def get_track(self, obj):
        raw_track = TagTrack.objects.filter(tag=obj, created__gte=(timezone.now() - timedelta(days=2))).order_by('id')
        track = []
        for raw_position in raw_track:
            position: TagTrack = raw_position
            data = [x for x in [
                (position.reader1, position.distance1),
                (position.reader2, position.distance2),
                (position.reader3, position.distance3),
            ] if x[0] is not None]
            if len(data) == 0:
                continue
            sorted(data, key=lambda x: x[1], reverse=True)
            if len(track) > 0 and (abs(data[0][0].x - track[-1][0]) < 2 and abs(data[0][0].y - track[-1][1]) < 2):
                continue
            track.append((data[0][0].x, data[0][0].y, position.created))
        return track


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
        read_only_fields = ('belongs_to',)


class TagCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TagCategory
        fields = (
            'id',
            'name',
            'parent_category',
            'color',
            'device'
        )


class ClassifiedTagCategorySerializer(TagCategorySerializer):
    tags = TagSerializer(many=True, read_only=True)
    device = DeviceSerializer(read_only=True)

    class Meta(TagCategorySerializer.Meta):
        fields = TagCategorySerializer.Meta.fields + (
            'tags',
        )
        read_only_fields = ('tags', )


class EventSerializer(serializers.ModelSerializer):
    tag = TagSerializer(read_only=True)
    caused_by = serializers.CharField(source='get_caused_by_display')

    class Meta:
        model = Event
        fields = (
            'id',
            'name',
            'created',
            'caused_by',
            'tag'
        )
