import unittest
from types import SimpleNamespace
from launch import select_port

def port(name, vid=None, pid=None, description=""):
    return SimpleNamespace(device=name, vid=vid, pid=pid, description=description)

class PortSelectionTests(unittest.TestCase):
    def test_cp210x_not_builtin(self):
        self.assertEqual(select_port([port("COM1"),port("COM2"),port("COM3",0x10C4,0xEA60)]),"COM3")
    def test_other_port_number(self):
        self.assertEqual(select_port([port("COM8",0x10C4,0xEA60)]),"COM8")
    def test_missing(self):
        with self.assertRaises(RuntimeError): select_port([port("COM1"),port("COM2")])
    def test_multiple(self):
        self.assertEqual(select_port([port("COM3",0x10C4,0xEA60),port("COM8",0x10C4,0xEA60)],choose=lambda _: "com8"),"COM8")
    def test_invalid_selection(self):
        with self.assertRaises(RuntimeError): select_port([port("COM3",0x10C4,0xEA60),port("COM8",0x10C4,0xEA60)],choose=lambda _: "COM1")
    def test_override(self):
        self.assertEqual(select_port([port("COM9")],"com9"),"COM9")
    def test_missing_override(self):
        with self.assertRaises(RuntimeError): select_port([port("COM3")],"COM9")

if __name__ == "__main__":
    unittest.main()
