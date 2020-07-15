#!/usr/bin/env python
import json
import os
import struct
from multiprocessing import Process

import django
from dateutil.parser import parse
from kafka import KafkaConsumer, TopicPartition
from kafka.consumer.fetcher import ConsumerRecord


def parse_tags_byte_stream(tags_byte_stream: bytes):
    """
    frame format:
    tagId  reader1Id reader1Pos reader2Id reader2Pos reader3Id reader3Pos
    01 02  03 04     05 06      07 08     09 10      11 12     13 14
    00 01  00 00     00 6d      ff ff     00 00      ff ff     00 00
    """
    if len(tags_byte_stream) % 14 != 0:
        print('malformed tag stream format, len={}'.format(len(tags_byte_stream)))
        # malformed tag stream format
        return None
    tags = []
    while len(tags_byte_stream) > 0:
        frame = tags_byte_stream[:14]
        tags.append(struct.unpack('>HHHHHHH', frame))
        tags_byte_stream = tags_byte_stream[14:]
    return tags


def get_reader(reader_rid, device):
    from tag.models import Reader

    if reader_rid == 0xFFFF:
        return None

    return Reader.objects.get_or_create(rid=reader_rid, device=device, defaults={
        'x': 0,
        'y': 0,
        'name': 'READER_{}'.format(reader_rid)
    })[0]


def property_loop_start():
    from device.models import Device
    from tag.models import Tag, TagTrack
    from tag.services import run_callbacks

    consumer = KafkaConsumer(bootstrap_servers=(
        '124.70.129.107:9094',
        '124.70.193.90:9094',
        '124.70.217.193:9094 '
    ))
    topic = TopicPartition(topic='saveProps', partition=2)
    consumer.assign([topic])
    for msg in consumer:
        try:
            print('save prop req')
            target: ConsumerRecord = msg
            data = json.loads(target.value)
            raw_tags = data['services'][0]['properties']['tags']
            print(raw_tags)
            if raw_tags is None:
                tags = []
            else:
                tags = parse_tags_byte_stream(bytes.fromhex(raw_tags))
                if tags is None:
                    continue

            try:
                device = Device.objects.get(device_id=data['device_id'])
            except Device.DoesNotExist:
                print('Unknown device with ID: {}'.format(data['device_id']))
                continue

            event_time = parse(data['services'][0]['event_time'])

            detected_tags = []
            for tid, reader1_id, reader1_dis, reader2_id, reader2_dis, reader3_id, reader3_dis in tags:
                reader1 = get_reader(reader1_id, device)
                reader2 = get_reader(reader2_id, device)
                reader3 = get_reader(reader3_id, device)

                tag = Tag.objects.get_or_create(tid=tid, device=device, defaults={
                    'name': 'TAG_' + str(tid)
                })[0]
                TagTrack.objects.create(
                    tag=tag,

                    reader1=reader1,
                    distance1=reader1_dis,
                    reader2=reader2,
                    distance2=reader2_dis,
                    reader3=reader3,
                    distance3=reader3_dis,

                    created=event_time
                )
                tag.is_online = True
                tag.save()
                detected_tags.append(tag.id)

            # 存在性检测
            # 规则：只检查active标签、active基站且原本online标签的存在性
            invalid_tags = Tag.objects\
                .filter(
                    device=device,
                    device__is_active=True,
                    is_active=True,
                    is_online=True
                )\
                .exclude(id__in=detected_tags)
            invalid_tags_all = list(invalid_tags.all())
            invalid_tags.update(is_online=False)
            for tag in invalid_tags_all:
                print('Callback run: Tag {}'.format(tag))
                run_callbacks(tag, 'lost_signal')

        except (TypeError, KeyError, json.JSONDecodeError):
            print('Malformed data: {}'.format(msg))


def watch_config_sync_req():
    from device.iot import tag_sync_conf
    from tag.models import Tag

    consumer = KafkaConsumer(bootstrap_servers=(
        '124.70.129.107:9094',
        '124.70.193.90:9094',
        '124.70.217.193:9094 '
    ))
    topic = TopicPartition(topic='watchConfigSyncReq', partition=2)
    consumer.assign([topic])
    for msg in consumer:
        try:
            print(msg)
            print('conf sync req')
            target: ConsumerRecord = msg
            data = json.loads(target.value)
            tid, = struct.unpack('>H', bytearray(data['data'][1:], 'ascii'))
            try:
                tag = Tag.objects.get(tid=tid)
            except Tag.DoesNotExist:
                continue

            tag_sync_conf(tag)

        except (TypeError, KeyError, json.JSONDecodeError):
            print('Malformed data: {}'.format(msg))


def watch_sensor_exception():
    from tag.models import Tag
    from tag.services import run_callbacks

    consumer = KafkaConsumer(bootstrap_servers=(
        '124.70.129.107:9094',
        '124.70.193.90:9094',
        '124.70.217.193:9094 '
    ))
    topic = TopicPartition(topic='sensorException', partition=2)
    consumer.assign([topic])
    mapping = {
        0: 'unmask',
        1: 'moved'
    }
    for msg in consumer:
        try:
            print('sensor exception req')
            target: ConsumerRecord = msg
            data = json.loads(target.value)
            tid, event_type = struct.unpack('>HB', bytearray(data['data'][1:], 'ascii'))
            try:
                tag = Tag.objects.get(tid=tid)
            except Tag.DoesNotExist:
                continue
            print('Callback run: Tag {}'.format(tag))
            run_callbacks(tag, mapping[event_type])

        except (TypeError, KeyError, json.JSONDecodeError):
            print('Malformed data: {}'.format(msg))


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intellikeeper_api.settings')
    django.setup()

    detectors = {
        Process(target=property_loop_start),
        Process(target=watch_config_sync_req),
        Process(target=watch_sensor_exception)
    }
    for detector in detectors:
        detector.start()
    for detector in detectors:
        detector.join()


if __name__ == '__main__':
    main()
