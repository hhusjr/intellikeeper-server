import base64
import json

from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


def call_device(uid, action, params=None):
    if params is None:
        params = {}

    params['action'] = action

    try:
        client = AcsClient(AliyunSettings.access_key_id, AliyunSettings.access_key_secret, AliyunSettings.iot_area)

        request = CommonRequest()
        request.set_accept_format('json')
        request.set_method('POST')
        request.set_domain('iot.cn-shanghai.aliyuncs.com')
        request.set_protocol_type('https')
        request.set_version('2018-01-20')
        request.set_action_name('RRpc')

        request.add_query_param('RegionId', AliyunSettings.iot_area)
        request.add_query_param('DeviceName', '{}{}'.format(AliyunSettings.iot_device_pre, uid))
        request.add_query_param('Timeout', '6000')
        request.add_query_param('RequestBase64Byte', base64.b64encode(bytes(json.dumps(params), encoding='utf8')))
        request.add_query_param('ProductKey', AliyunSettings.iot_product_id)
        request.add_query_param('Topic', '/request')

        result = json.loads(client.do_action_with_exception(request))
        print('{}{}'.format(AliyunSettings.iot_device_pre, uid))
        print(result)

        payload = base64.b64decode(result['PayloadBase64Byte'])
        response = json.loads(payload)
        print(response)

        return response
    except (ServerException, KeyError):
        return None


