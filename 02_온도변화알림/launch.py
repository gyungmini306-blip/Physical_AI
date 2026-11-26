"""One-click Windows launcher for the temperature monitoring assignment."""
import argparse
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTTP_PORT = 5000

def candidates(ports):
    """Return only known Silicon Labs CP210x USB-UART ports."""
    return sorted({p.device for p in ports
                   if (p.vid, p.pid) == (0x10C4, 0xEA60)
                   or (p.vid == 0x10C4 and "CP210" in (p.description or "").upper())})

def select_port(ports, override=None, choose=input):
    ports = list(ports)
    if override:
        override = override.upper()
        if not re.fullmatch(r"COM[1-9][0-9]*", override):
            raise RuntimeError("Invalid COM port.")
        if override not in {p.device.upper() for p in ports}:
            raise RuntimeError(f"{override} is not connected.")
        return override
    found = candidates(ports)
    if len(found) == 1:
        return found[0]
    if not found:
        raise RuntimeError("No CP210x ESP32 detected. Check USB cable and Device Manager. For another USB-UART adapter use start-server.cmd COMx.")
    print("Multiple CP210x devices found:", ", ".join(found))
    answer = choose("Enter ESP32 COM port: ").strip().upper()
    if answer not in found:
        raise RuntimeError("Select a listed CP210x port.")
    return answer

def main():
    parser = argparse.ArgumentParser(description="Start MariaDB and temperature dashboard")
    parser.add_argument("port", nargs="?", help="Optional manual COM port")
    parser.add_argument("--history", action="store_true", help="View saved data without USB")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--ide", action="store_true", help="Open Arduino sketch")
    modes.add_argument("--db", choices=["start","check","console","selftest","stop"], help="MariaDB management")
    modes.add_argument("--menu", action="store_true", help="Show optional maintenance menu")
    args = parser.parse_args()
    if args.menu:
        print("1. Live dashboard\n2. Open Arduino sketch\n3. Saved history\n4. SQL console\n5. Test database\n6. Stop database\n0. Exit")
        choice = input("Select: ").strip()
        if choice == "0": return 0
        if choice == "2": args.ide = True
        elif choice == "3": args.history = True
        elif choice == "4": args.db = "console"
        elif choice == "5": args.db = "selftest"
        elif choice == "6": args.db = "stop"
        elif choice != "1": raise RuntimeError("Unknown menu selection.")
    if (args.ide or args.db) and (args.history or args.port):
        parser.error("Choose a single action.")
    if args.ide:
        kit = Path(os.environ["LOCALAPPDATA"]) / "ESP32SchoolKit"
        ide = next((kit / "apps" / "arduino-ide").rglob("Arduino IDE.exe"), None)
        if ide is None: raise RuntimeError("Arduino IDE not found.")
        sketch = ROOT / "sketches" / "TemperatureAlert" / "TemperatureAlert.ino"
        subprocess.Popen([str(ide), str(sketch)], cwd=sketch.parent)
        print("Arduino IDE opened; select ESP32 Dev Module and actual COM port; upload manually.")
        return 0
    if args.db:
        script = ROOT / "MariaDB_설정" / "native_db.py"
        if args.db in ("console","selftest"):
            subprocess.run([sys.executable, str(script), "start"], check=True)
        return subprocess.call([sys.executable, str(script), args.db])
    from serial.tools import list_ports
    if args.history and args.port:
        parser.error("--history and COM port cannot be combined")
    # Detect before starting DB; never probe or open unrelated COM ports.
    port = None if args.history else select_port(list_ports.comports(), args.port)
    if port:
        print("ESP32 detected:", port, flush=True)
    else:
        print("History-only mode", flush=True)
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", HTTP_PORT)) == 0:
            raise RuntimeError("Port 5000 is already in use. Close the existing dashboard server before starting again.")
    # The native DB script preserves existing credentials/data and checks connectivity.
    subprocess.run([sys.executable, str(ROOT / "MariaDB_설정" / "native_db.py"), "start"], check=True)
    command = [sys.executable, str(ROOT / "server" / "app.py"),
               "--backend", "mariadb", "--open-browser", "--http-port", str(HTTP_PORT)]
    if port:
        command.extend(["--port", port])
    print("Dashboard: http://127.0.0.1:5000", flush=True)
    print("Close Arduino Serial Monitor before starting. Ctrl+C to stop.", flush=True)
    return subprocess.call(command)

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nDashboard stopped. MariaDB and stored records retained.")
    except (RuntimeError, OSError, ImportError, subprocess.CalledProcessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
