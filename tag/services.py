from tag.models import Trigger, Callback
import json
import requests
from tag import triggers


def parse_trigger_req_str(s:str, context):
    replacements = {
        'tag_name': context['tag'].name,
        'tag_tid': context['tag'].tid,
        'device_uid': context['tag'].device.uid,
        'device_name': context['tag'].device.name
    }
    for source, replacement in replacements.items():
        s = s.replace('{% ' + source + ' %}', replacement)
    return s


def invoke_trigger(trigger:Trigger, context):
    if not trigger.is_active:
        return

    params = json.loads(trigger.callback_params)
    if not isinstance(params, dict):
        return
    params = {k: parse_trigger_req_str(v, context) for k, v in params.items()}

    # 先考虑是否为内部回调
    if trigger.callback_protocol == 'intellikeeper':
        # 直接调用内部方法
        internal_methods = {
            'sms-alarm': triggers.sms_alarm,
            'email-alarm': triggers.email_alarm
        }
        if trigger.callback_url not in internal_methods:
            return
        internal_methods[trigger.callback_url](context['tag'], params)
        return

    # 否则请求外部URL
    headers = json.loads(trigger.callback_headers)
    if not isinstance(headers, dict):
        return
    headers = {k: parse_trigger_req_str(v, context) for k, v in headers.items()}

    callback_url = parse_trigger_req_str(trigger.callback_url, context)
    callback_url = '{}://{}'.format(trigger.callback_protocol, callback_url)

    method = trigger.callback_method
    method_maping = {
        1: 'get',
        2: 'post',
        3: 'put'
    }

    requests.request(method_maping[method], callback_url, headers=headers, data=params)


def handle_callbacks(callbacks:[Callback], request, tag):
    for callback in callbacks:
        if callback.is_active:
            invoke_trigger(callback.trigger, {
                'request': request,
                'tag': tag
            })
