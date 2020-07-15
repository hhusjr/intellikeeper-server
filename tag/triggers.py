from django.core.mail import send_mail
from twilio.rest import Client

from intellikeeper_api.settings import DEFAULT_FROM_EMAIL, SMS_NUMBER
from tag.events import get_desc_by_event
from tag.facade import tag_get_path


def get_message(tag, event):
    return '智能管家警告：您的物品【{}/{}】可能已经被盗（基站名称：{}，基站位置：{}），原因：【{}】。请登录智能管家查看详情。'.format(tag_get_path(tag),
                                                                                tag.name,
                                                                                tag.device.name,
                                                                                tag.device.location,
                                                                                get_desc_by_event(event)[1])

def get_message_en(tag, event):
    return 'IntelliKeeper Warning: A tag is under abnormal condition.'


def sms_alarm(tag, event, params):
    if 'send_to' not in params:
        return
    client = Client()
    client.messages.create(
        from_=SMS_NUMBER,
        to=params['send_to'],
        body=get_message_en(tag, event)
    )


def email_alarm(tag, event, params):
    if 'mail_to' not in params:
        return
    send_mail('智能管家警告', get_message(tag, event), DEFAULT_FROM_EMAIL, [params['mail_to']])
