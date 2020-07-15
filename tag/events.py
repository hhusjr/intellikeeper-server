EVENTS = {
    'test': (0, '测试'),
    'lost_signal': (1, '信号丢失'),
    'moved': (2, '标签被移'),
    'unmask': (3, '标签被取下')
}


def get_event_by_id(id):
    for k, v in EVENTS.items():
        if v[0] == id:
            return k
    return None


def get_desc_by_event(event):
    if event not in EVENTS:
        return None
    return EVENTS[event]
