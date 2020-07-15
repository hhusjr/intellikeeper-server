import json

import requests

from tag import triggers
from tag.events import get_desc_by_event
from tag.facade import tag_get_path
from tag.models import Trigger, Callback, TagCategory, Event


def tag_get_sub_categories(category: TagCategory):
    result = [category]

    if category is None:
        return result

    children = TagCategory.objects.filter(parent_category=category)
    for child in children:
        result.extend(tag_get_sub_categories(child))

    return result


def parse_trigger_req_str(s: str, tag, event):
    replacements = {
        'tag_name': tag.name,
        'tag_tid': str(tag.tid),
        'device_id': tag.device.device_id,
        'device_name': tag.device.name,
        'tag_path': tag_get_path(tag),
        'event_type': str(get_desc_by_event(event)[0])
    }
    for source, replacement in replacements.items():
        s = s.replace('{% ' + source + ' %}', replacement)
    return s


def invoke_trigger(trigger: Trigger, tag, event):
    if not trigger.is_active:
        return

    params = json.loads(trigger.callback_params)
    if not isinstance(params, dict):
        return
    params = {k: parse_trigger_req_str(v, tag, event) for k, v in params.items()}

    # 先考虑是否为内部回调
    if trigger.callback_protocol == 'intellikeeper':
        # 直接调用内部方法
        internal_methods = {
            'sms-alarm': triggers.sms_alarm,
            'email-alarm': triggers.email_alarm
        }
        if trigger.callback_url not in internal_methods:
            return
        internal_methods[trigger.callback_url](tag, event, params)
        return

    # 否则请求外部URL
    headers = json.loads(trigger.callback_headers)
    if not isinstance(headers, dict):
        return
    headers = {k: parse_trigger_req_str(v, tag, event) for k, v in headers.items()}

    callback_url = parse_trigger_req_str(trigger.callback_url, tag, event)
    callback_url = '{}://{}'.format(trigger.callback_protocol, callback_url)

    method = trigger.callback_method
    method_maping = {
        1: 'get',
        2: 'post',
        3: 'put'
    }

    requests.request(method_maping[method], callback_url, headers=headers, data=params)


def handle_callbacks(callbacks: [Callback], tag, event):
    for callback in callbacks:
        if callback.is_active:
            invoke_trigger(callback.trigger, tag, event)


def run_callbacks(tag, event):
    # 首先计入事件信息中
    desc = get_desc_by_event(event)
    Event.objects.create(
        name=('{}{}'.format(tag.name, desc[1])),
        caused_by=desc[0],
        tag=tag
    )

    # 根据冒泡原则：标签callback -> 分类树（一直到根节点）callback -> 基站callback -> 用户区块callback
    # 首先运行标签级别的callback
    callbacks = Callback.objects.filter(scope=4, target=tag.id).all()
    handle_callbacks(callbacks, tag, event)

    # 然后运行分类树上的所有callback
    category: TagCategory = tag.category
    while category is not None:
        callbacks = Callback.objects.filter(scope=3, target=category.id).all()
        handle_callbacks(callbacks, tag, event)
        category = category.parent_category

    # 然后运行基站层面的callback
    callbacks = Callback.objects.filter(scope=2, target=tag.device.id).all()
    handle_callbacks(callbacks, tag, event)

    # 然后运行全局callback
    uid = tag.device.belongs_to.id
    callbacks = Callback.objects.filter(scope=1, target=uid).all()
    handle_callbacks(callbacks, tag, event)
