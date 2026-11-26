"""Shared USB/BLE line protocol and duplicate-suppression state."""
import json
from collections import deque

MAX_LINE = 4096

class JsonLines:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer.extend(data)
        if len(self.buffer) > MAX_LINE and b'\n' not in self.buffer:
            self.buffer.clear()
            return []
        results = []
        while b'\n' in self.buffer:
            line, _, rest = self.buffer.partition(b'\n')
            self.buffer = bytearray(rest)
            try:
                item = json.loads(line.decode('utf-8').strip())
            except (UnicodeError, ValueError):
                continue
            if isinstance(item, dict) and 'seq' in item:
                results.append(item)
        return results

class State:
    def __init__(self):
        self.latest = {}
        self.events = deque(maxlen=100)
        self.last_event_id = -1
        self.last_seq = -1
        self.boot_epoch = 0

    def update(self, item):
        seq = int(item.get('seq', -1))
        sec = int(item.get('sec', 0))
        if seq < self.last_seq and sec < int(self.latest.get('sec', 0)):
            self.boot_epoch += 1
            self.last_event_id = -1
            self.last_seq = -1
        if seq <= self.last_seq:
            return False
        self.last_seq = seq
        self.latest = item
        event_id = int(item.get('eventId', 0))
        if event_id > self.last_event_id:
            self.last_event_id = event_id
            name = item.get('event', '')
            if name and name != 'BOOT':
                self.events.appendleft((sec, name))
        return True
