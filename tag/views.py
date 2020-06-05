import json

from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from device.models import Device
from tag.serializers import TagSerializer, TriggerSerializer
from tag.models import Tag, Callback, Trigger
from device.services import call_device
from tag.apps import TagConfig
from tag.services import handle_callbacks, invoke_trigger


class TagViewset(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer

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

    def perform_create(self, serializer):
        new_tag_id = call_device(Device.objects.get(pk=self.request.data['device']).uid, 'new_tag')
        if new_tag_id['new_tag_tid'] is None:
            raise ValidationError({
                'tid': ['无法识别到标签，请将标签靠近基站再试。']
            })

        serializer.save(tid=new_tag_id['new_tag_tid'])


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
    res = call_device(tag.device.uid, 'activate_tag' if new_is_active else 'deactivate_tag', {
        'tid': tag.tid
    })

    if res is None or 'success' not in res:
        return Response({
            'success': False
        })

    tag.is_active = True if new_is_active else False
    tag.save()

    return Response({
        'success': True
    })


@api_view(('POST',))
def dead_tags(request):
    key = request.data.get('key', None)
    base_id = request.data.get('base_id', None)
    print(request.data.get('dead_tags', '[]'))
    dead_tags_list = json.loads(request.data.get('dead_tags', '[]'))

    if key != TagConfig.key_dead_tags:
        return Response(status=status.HTTP_403_FORBIDDEN)

    for tid in dead_tags_list:
        try:
            tag = Tag.objects.get(tid=tid)
            if tag.device.uid != base_id:
                continue

            if not tag.is_active:
                continue

            # First, run GLOBAL triggers
            uid = tag.device.belongs_to.id
            callbacks = Callback.objects.filter(scope=1, target=uid).all()
            handle_callbacks(callbacks, request, tag)

            # Then, run BASE-LEVEL triggers
            callbacks = Callback.objects.filter(scope=2, target=tag.device.id).all()
            handle_callbacks(callbacks, request, tag)

            # Then, run TAG-LEVEL triggers
            callbacks = Callback.objects.filter(scope=3, target=tag.id).all()
            handle_callbacks(callbacks, request, tag)

        except Tag.DoesNotExist:
            continue

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

    invoke_trigger(trigger, {
        'tag': tag,
        'request': request
    })

    return Response()


class CallbackView(views.APIView):
    permission_classes = (permissions.IsAuthenticated, )

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

        # 标签的触发器
        if scope == 3:
            try:
                tag = Tag.objects.get(pk=target, device__belongs_to=request.user)
            except Tag.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            callback_trigger_ids = Callback.objects.filter(scope=3, target=tag.id).values_list('trigger_id', flat=True)
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

        # 标签的触发器
        if scope == 3:
            try:
                tag = Tag.objects.get(pk=target, device__belongs_to=request.user)
            except Tag.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            Callback.objects.create(scope=3, target=tag.id, trigger=trigger)
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
            except Trigger.DoesNotExist:
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
            except Trigger.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response()

        # 标签的触发器
        if scope == 3:
            try:
                tag = Tag.objects.get(pk=target, device__belongs_to=request.user)
            except Tag.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            try:
                o = Callback.objects.get(scope=3, target=tag.id, trigger=trigger)
                o.delete()
            except Trigger.DoesNotExist:
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


@api_view(('GET', ))
@permission_classes((permissions.IsAuthenticated, ))
def get_readers_pos(request):
    try:
        device = Device.objects.get(pk=request.query_params.get('device'), belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    result = call_device(device.uid, 'get_readers_pos')
    if result is None:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(result)


@api_view(('GET', ))
@permission_classes((permissions.IsAuthenticated, ))
def get_track(request, pk):
    try:
        tag = Tag.objects.get(pk=pk, device__belongs_to=request.user)
    except Tag.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    result = call_device(tag.device.uid, 'get_track', {
        'tid': tag.tid
    })
    if result is None:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(result)
