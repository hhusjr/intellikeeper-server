from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from device.serializers import DeviceSerializer
from device.models import Device
from device.services import handshake_with, call_device


class DeviceViewset(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return Device.objects.filter(belongs_to=self.request.user)

    def perform_create(self, serializer):
        serializer.save(belongs_to=self.request.user)

    def perform_update(self, serializer):
        serializer.save(belongs_to=self.request.user)


@api_view(('GET', ))
@permission_classes((permissions.IsAuthenticated, ))
def handshake_with_device(request, pk):
    try:
        device = Device.objects.get(pk=pk, belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    uid = device.uid
    return Response({
        'status': handshake_with(uid)
    })


@api_view(('PUT', ))
@permission_classes((permissions.IsAuthenticated, ))
def change_device_status(request, pk):
    try:
        device = Device.objects.get(pk=pk, belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    uid = device.uid

    new_is_active = request.data.get('new_status', 'false') == 'true'
    res = call_device(uid, 'activate' if new_is_active else 'deactivate')

    if res is None or 'success' not in res:
        return Response({
            'success': False
        })

    device.is_active = True if new_is_active else False
    device.save()

    return Response({
        'success': True
    })
