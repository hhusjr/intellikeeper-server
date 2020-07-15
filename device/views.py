from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from device.models import Device
from device.serializers import DeviceSerializer, FullDeviceSerializer
from device.services import call_device


class DeviceViewset(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FullDeviceSerializer

    def get_queryset(self):
        return Device.objects.filter(belongs_to=self.request.user)

    def perform_create(self, serializer):
        serializer.save(belongs_to=self.request.user)

    def perform_update(self, serializer):
        serializer.save(belongs_to=self.request.user)


@api_view(('PUT',))
@permission_classes((permissions.IsAuthenticated,))
def change_device_status(request, pk):
    try:
        device = Device.objects.get(pk=pk, belongs_to=request.user)
    except Device.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    new_is_active = request.data.get('new_status', 'false') == 'true'

    device.is_active = True if new_is_active else False
    device.save()

    return Response({
        'success': True
    })
