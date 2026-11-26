"""Single entry point for all existing SmartHomeCare examples."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KIT = Path(os.environ["LOCALAPPDATA"]) / "ESP32SchoolKit"
SKETCHES = {
    "1": ROOT / "sketches" / "SmartHomeCare" / "SmartHomeCare.ino",
    "2": ROOT / "sketches" / "SmartHomeCarePlus" / "SmartHomeCarePlus.ino",
    "3": ROOT / "sketches" / "SmartHomeCarePlusBuzzer" / "SmartHomeCarePlusBuzzer.ino",
    "4": ROOT / "esp32-dual-connection" / "sketches" / "SmartHomeCare" / "SmartHomeCare.ino",
}

def open_ide(sketch):
    ide = next((KIT / "apps" / "arduino-ide").rglob("Arduino IDE.exe"), None)
    if ide is None:
        raise RuntimeError("Arduino IDE not found.")
    subprocess.Popen([str(ide), str(sketch)], cwd=sketch.parent)

def choose_port():
    from serial.tools import list_ports
    found = sorted({p.device for p in list_ports.comports()
        if (p.vid, p.pid) == (0x10C4, 0xEA60)
        or (p.vid == 0x10C4 and "CP210" in (p.description or "").upper())})
    if len(found) == 1:
        return found[0]
    if not found:
        raise RuntimeError("No CP210x board detected. Check USB and Device Manager.")
    print("Detected:", ", ".join(found))
    port = input("ESP32 COM port: ").strip().upper()
    if port not in found:
        raise RuntimeError("Select a detected port.")
    return port

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=["1","2","3","4","5","6","0"])
    args = parser.parse_args()
    mode = args.mode
    if mode is None:
        print("\n1. Basic Arduino sketch\n2. Wi-Fi PLUS\n3. Wi-Fi PLUS + buzzer\n4. USB/BLE Arduino sketch\n5. USB/BLE PC dashboard\n6. BLE-only PC dashboard\n0. Exit")
        mode = input("Select: ").strip()
    if mode == "0":
        return 0
    if mode in SKETCHES:
        open_ide(SKETCHES[mode])
        print("Arduino IDE opened. Select ESP32 Dev Module and actual COM port; upload manually.")
        return 0
    if mode in ("5","6"):
        port = choose_port() if mode == "5" else ""
        print("Upload the USB/BLE sketch (option 4) and close Serial Monitor first.", flush=True)
        return subprocess.call([sys.executable, str(ROOT / "esp32-dual-connection" / "pc" / "dashboard.py"), "--port", port])
    raise RuntimeError("Unknown menu selection.")

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError, ImportError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
