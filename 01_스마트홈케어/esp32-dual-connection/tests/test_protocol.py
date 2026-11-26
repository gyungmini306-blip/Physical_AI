import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pc'))
from protocol import JsonLines, State

class ProtocolTests(unittest.TestCase):
    def test_partial_packets(self):
        p = JsonLines()
        self.assertEqual(p.feed(b'{"seq":1,"pir":'), [])
        self.assertEqual(p.feed(b'true}\n'), [{'seq':1, 'pir':True}])
    def test_duplicate(self):
        state = State()
        frame = {'seq':1, 'sec':1, 'eventId':1, 'event':'PIR MOTION'}
        self.assertTrue(state.update(frame))
        self.assertFalse(state.update(frame))
        self.assertEqual(len(state.events), 1)
    def test_reset(self):
        state = State()
        state.update({'seq':8,'sec':20,'eventId':3,'event':'PIR CLEAR'})
        self.assertTrue(state.update({'seq':1,'sec':0,'eventId':1,'event':'BOOT'}))
    def test_invalid_line(self):
        p = JsonLines()
        self.assertEqual(p.feed(b'not json\n'), [])

if __name__ == '__main__':
    unittest.main()
