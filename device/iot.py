import json
import logging
import struct

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.client import ClientBuilder
from huaweicloudsdkcore.exceptions.exceptions import ClientRequestException
from huaweicloudsdkcore.http.http_config import HttpConfig
from huaweicloudsdkiotda.v5 import IoTDAClient, ShowDeviceRequest, ShowDeviceResponse, CreateCommandRequest, \
    CreateCommandResponse

from device.models import Device
from intellikeeper_api.hwyun_settings import HwyunSettings
from tag.models import Tag, Reader


def get_iot_client():
    config = HttpConfig.get_default_config()
    credentials = BasicCredentials(HwyunSettings.access_key_id, HwyunSettings.access_key_secret, HwyunSettings.project_id, HwyunSettings.domain_id)
    builder: ClientBuilder = IoTDAClient().new_builder(IoTDAClient)
    client: IoTDAClient = builder.with_http_config(config) \
        .with_credentials(credentials) \
        .with_endpoint(HwyunSettings.endpoint) \
        .with_stream_log(log_level=logging.INFO) \
        .build()
    return client


def check_base_online(device_id):
    client = get_iot_client()
    res: ShowDeviceResponse = client.show_device(ShowDeviceRequest(device_id=device_id))
    return res.status == 'ONLINE'


def tag_sync_conf(tag: Tag):
    client = get_iot_client()
    try:
        result: CreateCommandResponse = client.create_command(CreateCommandRequest(tag.device.device_id, body={
            'command_name': 'sensorChoose',
            'paras': {
                'accSensor': tag.move_detect_on,
                'lightSensor': tag.light_detect_on,
                'tagId': tag.tid,
                'muteMode': tag.mute_mode_on
            } if tag.is_active and tag.device.is_active else {
                'accSensor': False,
                'lightSensor': False,
                'tagId': tag.tid,
                'muteMode': 1
            }
        }))
    except ClientRequestException as e:
        return 1, e.error_msg

    return result.response['result_code'], result.response


def get_readers(device: Device):
    client = get_iot_client()
    try:
        result: CreateCommandResponse = client.create_command(CreateCommandRequest(device.device_id, body={
            'command_name': 'getReaders',
            'paras': {}
        }))
    except ClientRequestException as e:
        return 1, e.error_msg

    if result.response['result_code'] != 0:
        return 1, 'Error'

    readers = result.response['paras']['readers']
    if len(readers) % 4 != 0:
        return 1, 'Malformed package'

    while len(readers) > 0:
        reader, = struct.unpack('<H', bytes.fromhex(readers[:4]))
        Reader.objects.get_or_create(rid=reader, device=device, defaults={
            'x': 0,
            'y': 0,
            'name': 'READER_{}'.format(reader)
        })
        readers = readers[4:]
    return 0, result.response
