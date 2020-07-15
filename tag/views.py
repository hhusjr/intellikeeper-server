from django_filters import rest_framework as drf_filter
from huaweicloudsdkcore.exceptions.exceptions import ServerResponseException
from huaweicloudsdkiotda.v5 import ListPropertiesRequest
from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from device.iot import get_iot_client, tag_sync_conf, get_readers
from device.models import Device
from device.services import call_device
from intellikeeper_api.hwyun_settings import HwyunSettings
from tag.models import Tag, Callback, Trigger, TagCategory, Reader, Event
from tag.serializers import TagSerializer, TriggerSerializer, TagCategorySerializer, ReaderSerializer, \
    ClassifiedTagCategorySerializer, TrackedTagSerializer, EventSerializer
from tag.services import invoke_trigger, tag_get_sub_categories, run_callbacks


class TagFilter(drf_filter.FilterSet):
    category = drf_filter.NumberFilter(method='filter_category')

    def filter_category(self, queryset, name, value):
        try:
            category = TagCategory.objects.get(pk=value)
        except TagCategory.DoesNotExist:
            return queryset
        return queryset.filter(category__in=tag_get_sub_categories(category))


class TagViewset(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer

    filter_backends = (drf_filter.DjangoFilterBackend, )
    filterset_class = TagFilter

    def get_queryset(self):
        if 'device' not in self.request.query_params:
            raise ValidationError

        device_id = self.request.query_params['device']
        try:
            device = Device.objects.get(pk=device_id, belongs_to=self.request.user)
            return Tag.objects.filter(device=device)
        except Device.DoesNotExist:
            raise ValidationError

    def get_serializer_context(self):
        return {
            'request': self.request
        }

    def perform_update(self, serializer: TagSerializer):
        tag_sync_conf(serializer.save())


class ReaderViewset(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReaderSerializer

    def get_queryset(self):
        if 'device' not in self.request.query_params:
            raise ValidationError

        device_id = self.request.query_params['device']
        try:
            device = Device.objects.get(pk=device_id, belongs_to=self.request.user)
            return Reader.objects.filter(device=device)
        except Device.DoesNotExist:
            raise ValidationError

    def list(self, request, *args, **kwargs):
        device_id = self.request.query_params['device']
        try:
            device = Device.objects.get(pk=device_id, belongs_to=self.request.user)
        except Device.DoesNotExist:
            raise ValidationError

        # 先同步readers
        get_readers(device)

        return super().list(request, *args, **kwargs)

    def get_serializer_context(self):
        return {
            'request': self.request
        }


@api_view(('GET', ))
@permission_classes((permissions.IsAuthenticated, ))
def checkout_tags(request):
    try:
        device = Device.objects.get(pk=request.query_params.get('device'), belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # get all tags
    try:
        client = get_iot_client()
        return client.list_properties(ListPropertiesRequest(device.device_id, service_id=HwyunSettings.service_id))
    except ServerResponseException as e:
        print(e.error_msg)


@api_view(('GET',))
@permission_classes((permissions.IsAuthenticated,))
def find_tag(request, pk):
    try:
        tag = Tag.objects.get(pk=pk, device__belongs_to=request.user)
    except Tag.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    call_device(tag.device.uid, 'find_tag', {
        'tid': tag.tid
    })
    return Response()


@api_view(('PUT',))
@permission_classes((permissions.IsAuthenticated,))
def change_tag_status(request, pk):
    try:
        tag = Tag.objects.get(pk=pk, device__belongs_to=request.user)
    except Tag.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    new_is_active = request.data.get('new_status', 'false') == 'true'
    tag.is_active = True if new_is_active else False
    tag.save()
    tag_sync_conf(tag)

    return Response({
        'success': True
    })


@api_view(('GET', ))
def test_callback(request, pk):
    try:
        tag = Tag.objects.get(pk=pk, device__belongs_to=request.user)
    except Tag.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    run_callbacks(tag, 'test')
    return Response()


class TriggerViewset(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TriggerSerializer

    def get_queryset(self):
        return Trigger.objects.filter(belongs_to=self.request.user)

    def perform_create(self, serializer):
        serializer.save(belongs_to=self.request.user)

    # TODO: 防止修改时改到其他用户的情况（还有其他地方有类似情况需要检查！）


@api_view(('GET',))
@permission_classes((permissions.IsAuthenticated,))
def get_classified_tags(request):
    result_tags = {}

    tags = Tag.objects.filter(device__belongs_to=request.user).all()
    for tag in tags:
        if tag.device.id not in result_tags:
            result_tags[tag.device.id] = []
        result_tags[tag.device.id].append({
            'tid': tag.tid,
            'id': tag.id,
            'name': tag.name
        })

    devices = {device.id: {
        'name': device.name,
        'uid': device.uid
    } for device in Device.objects.filter(belongs_to=request.user)}

    return Response({
        'tags': result_tags,
        'devices': devices
    })


@api_view(('GET',))
@permission_classes((permissions.IsAuthenticated,))
def test_trigger(request, pk):
    try:
        tag = Tag.objects.get(pk=request.query_params.get('tag'), device__belongs_to=request.user)
    except Tag.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    try:
        trigger = Trigger.objects.get(pk=pk, belongs_to=request.user)
    except Trigger.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    invoke_trigger(trigger, tag, 'test')

    return Response()


class CallbackView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        scope = int(request.query_params.get('scope', 1))
        target = int(request.query_params.get('target', 0))

        # 全局触发器
        if scope == 1:
            callback_trigger_ids = Callback.objects.filter(scope=1, target=request.user.id,
                                                           trigger__belongs_to=request.user).values_list('trigger_id',
                                                                                                         flat=True)
            return Response(Trigger.objects.filter(id__in=callback_trigger_ids).values('id', 'name'))

        # 设备级触发器
        if scope == 2:
            try:
                device = Device.objects.get(pk=target, belongs_to=request.user)
            except Device.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            callback_trigger_ids = Callback.objects.filter(scope=2, target=device.id).values_list('trigger_id',
                                                                                                  flat=True)
            return Response(Trigger.objects.filter(id__in=callback_trigger_ids).values('id', 'name'))

        # 分类触发器
        if scope == 3:
            try:
                category = TagCategory.objects.get(pk=target, device__belongs_to=request.user)
            except Device.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            callback_trigger_ids = Callback.objects.filter(scope=3, target=category.id,
                                                           trigger__belongs_to=request.user).values_list('trigger_id',
                                                                                                         flat=True)
            return Response(Trigger.objects.filter(id__in=callback_trigger_ids).values('id', 'name'))

        # 标签的触发器
        if scope == 4:
            try:
                tag = Tag.objects.get(pk=target, device__belongs_to=request.user)
            except Tag.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            callback_trigger_ids = Callback.objects.filter(scope=4, target=tag.id).values_list('trigger_id', flat=True)
            return Response(Trigger.objects.filter(id__in=callback_trigger_ids).values('id', 'name'))

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        scope = int(request.query_params.get('scope', -1))
        target = int(request.query_params.get('target', -1))
        if scope < 0 or target < 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            trigger = Trigger.objects.get(pk=request.data.get('trigger'), belongs_to=request.user)
        except Trigger.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 全局触发器
        if scope == 1:
            Callback.objects.create(scope=1, target=request.user.id, trigger=trigger)
            return Response()

        # 设备级触发器
        if scope == 2:
            try:
                device = Device.objects.get(pk=target, belongs_to=request.user)
            except Device.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            Callback.objects.create(scope=2, target=device.id, trigger=trigger)
            return Response()

        # 分类级触发器
        if scope == 3:
            try:
                category = TagCategory.objects.get(pk=target, device__belongs_to=request.user)
            except Device.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            Callback.objects.create(scope=3, target=category.id, trigger=trigger)
            return Response()

        # 标签的触发器
        if scope == 4:
            try:
                tag = Tag.objects.get(pk=target, device__belongs_to=request.user)
            except Tag.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            Callback.objects.create(scope=4, target=tag.id, trigger=trigger)
            return Response()

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        scope = int(request.query_params.get('scope', -1))
        target = int(request.query_params.get('target', -1))
        if scope < 0 or target < 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            trigger = Trigger.objects.get(pk=request.data.get('trigger'), belongs_to=request.user)
        except Trigger.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 全局触发器
        if scope == 1:
            try:
                o = Callback.objects.get(scope=1, target=request.user.id, trigger=trigger)
                o.delete()
            except Callback.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response()

        # 设备级触发器
        if scope == 2:
            try:
                device = Device.objects.get(pk=target, belongs_to=request.user)
            except Device.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            try:
                o = Callback.objects.get(scope=2, target=device.id, trigger=trigger)
                o.delete()
            except Callback.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response()

        # 分类的触发器
        if scope == 3:
            try:
                category = TagCategory.objects.get(pk=target, device__belongs_to=request.user)
            except TagCategory.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            try:
                o = Callback.objects.get(scope=3, target=category.id, trigger=trigger)
                o.delete()
            except Callback.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response()

        # 标签的触发器
        if scope == 4:
            try:
                tag = Tag.objects.get(pk=target, device__belongs_to=request.user)
            except Tag.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            try:
                o = Callback.objects.get(scope=4, target=tag.id, trigger=trigger)
                o.delete()
            except Callback.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response()

        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(('PUT',))
@permission_classes((permissions.IsAuthenticated,))
def change_trigger_status(request, pk):
    try:
        trigger = Trigger.objects.get(pk=pk, belongs_to=request.user)
    except Trigger.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    trigger.is_active = request.data.get('new_status', 'false') == 'true'
    trigger.save()

    return Response()


@api_view(('GET',))
@permission_classes((permissions.IsAuthenticated,))
def get_tags_info(request):
    try:
        device = Device.objects.get(pk=request.query_params.get('device'), belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    result = call_device(device.uid, 'get_tags_info')
    if result is None:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    for i in range(len(result)):
        result[i]['name'] = Tag.objects.get(tid=result[i]['tid']).name

    return Response(result)


class TagCategoryViewset(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagCategorySerializer

    def get_queryset(self):
        if 'device' not in self.request.query_params:
            raise ValidationError

        device_id = self.request.query_params['device']
        try:
            device = Device.objects.get(pk=device_id, belongs_to=self.request.user)
            return TagCategory.objects.filter(device=device)
        except Device.DoesNotExist:
            raise ValidationError


@api_view(('GET', ))
@permission_classes((permissions.IsAuthenticated, ))
def get_classified_tags(request):
    try:
        device = Device.objects.get(pk=request.query_params.get('device'), belongs_to=request.user)
        qs = TagCategory.objects.filter(device=device)
    except Device.DoesNotExist:
        qs = TagCategory.objects.filter(device__belongs_to=request.user)

    return Response(ClassifiedTagCategorySerializer(qs, many=True).data)


@api_view(('GET', ))
@permission_classes((permissions.IsAuthenticated, ))
def get_track(request):
    try:
        device = Device.objects.get(pk=request.query_params.get('device'), belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(TrackedTagSerializer(
        TagFilter(request.GET, queryset=Tag.objects.filter(device=device)).qs,
        many=True
    ).data)


@api_view(('GET', ))
@permission_classes((permissions.IsAuthenticated, ))
def get_events(request):
    try:
        device = Device.objects.get(pk=request.query_params.get('device'), belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(EventSerializer(
        Event.objects.filter(tag__device=device),
        many=True
    ).data)


@api_view(('GET', ))
@permission_classes((permissions.IsAuthenticated, ))
def get_events_top10(request):
    try:
        device = Device.objects.get(pk=request.query_params.get('device'), belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(EventSerializer(
        Event.objects.filter(tag__device=device)[:10],
        many=True
    ).data)
