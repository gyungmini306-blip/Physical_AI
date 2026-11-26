import json
import tempfile
import unittest
from pathlib import Path
from database import Database, decode

class DatabaseTests(unittest.TestCase):
    def test_storage_and_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"test.db"
            db=Database(path)
            def frame(seq,temp,delta,state,alarm):
                return decode(json.dumps(dict(kind="temperature",boot="0123456789abcdef",
                    seq=seq,uptime_ms=seq*3000,temperature=temp,delta=delta,state=state,alarm=alarm)))
            a=frame(1,25,None,"WARMING_UP",False)
            b=frame(11,27,2,"RISING",True)
            c=frame(12,None,None,"SENSOR_ERROR",False)
            self.assertTrue(db.insert(a))
            self.assertTrue(db.insert(b))
            self.assertFalse(db.insert(b))
            self.assertTrue(db.insert(c))
            data=Database(path).snapshot()
            self.assertEqual(data["stats"]["samples"],3)
            self.assertEqual(data["stats"]["valid"],2)
            self.assertEqual(data["stats"]["average"],26)
            self.assertEqual(data["stats"]["alarms"],1)
            self.assertEqual(data["alarms"][0]["seq"],11)
            self.assertEqual(data["latest"]["state"],"SENSOR_ERROR")
            self.assertEqual(len(db.export_csv().splitlines()),4)
            self.assertEqual(db.snapshot("2099-01-01",None)["stats"]["samples"],0)
    def test_bad_frames(self):
        for line in ("ESP32 boot","{}", "[]", '{"kind":"temperature","boot":42}'):
            with self.assertRaises(ValueError): decode(line)

if __name__=="__main__":
    unittest.main()
