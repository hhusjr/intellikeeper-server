from django.core.mail import send_mail

from intellikeeper_api.settings import DEFAULT_FROM_EMAIL, SMS_NUMBER

from twilio.rest import Client


def sms_alarm(tag, params):
    if 'send_to' not in params:
        return
    client = Client()
    client.messages.create(
        from_=SMS_NUMBER,
        to=params['send_to'],
        body='您的物品{}可能已经被盗（基站名称：{}，基站位置：{}），请登录智能管家查看详情。'.format(tag.name,
                                                                 tag.device.name,
                                                                 tag.device.location)
    )


def email_alarm(tag, params):
    if 'mail_to' not in params:
        return
    send_mail('智能管家警告',
              '您的物品{}可能已经被盗（基站名称：{}，基站位置：{}），请登录智能管家查看详情。'.format(tag.name,
                                                                  tag.device.name,
                                                                  tag.device.location),
              DEFAULT_FROM_EMAIL, [params['mail_to']])
