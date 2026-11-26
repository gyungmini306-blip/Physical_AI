"""Local Flask dashboard; one serial reader, one SQLite database."""
import argparse
import logging
import threading
import time
import webbrowser
import urllib.request
from datetime import date, datetime, time as clock, timedelta, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request
from database import Database, decode

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "temperature.db"
LOG = logging.getLogger("temperature")

def date_bounds(day):
    # Date filter uses the PC's local calendar date; stored times use UTC.
    if not day:
        return None, None
    d = date.fromisoformat(day)
    return tuple(datetime.combine(x, clock.min).astimezone(timezone.utc).isoformat(timespec="milliseconds")
                 for x in (d, d + timedelta(days=1)))

def create_app(db, connection):
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/status")
    def status():
        try:
            bounds = date_bounds(request.args.get("date"))
        except (ValueError, OverflowError):
            return jsonify(error="Invalid date"), 400
        result = db.snapshot(*bounds)
        last = result["latest"]
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(last["received_at"])).total_seconds() if last else None
        result["connected"] = connection.is_set()
        result["live"] = connection.is_set() and age is not None and 0 <= age < 10
        return jsonify(result)

    @app.get("/api/export.csv")
    def export():
        try:
            bounds = date_bounds(request.args.get("date"))
        except (ValueError, OverflowError):
            return jsonify(error="Invalid date"), 400
        return Response("\ufeff" + db.export_csv(*bounds), content_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=temperature.csv"})
    return app

def read_serial(port, db, connected, stop):
    import serial
    while not stop.is_set():
        try:
            with serial.Serial(port, 115200, timeout=1) as ser:
                connected.set()
                LOG.info("Serial open: %s", port)
                buffer = bytearray()
                while not stop.is_set():
                    chunk = ser.read_until(b"\n", size=4096)
                    if not chunk:
                        continue
                    buffer.extend(chunk)
                    if len(buffer) > 4096:
                        buffer.clear()
                        continue
                    if not chunk.endswith(b"\n"):
                        continue
                    raw = bytes(buffer)
                    buffer.clear()
                    try:
                        frame = decode(raw.decode("utf-8"))
                    except (ValueError, UnicodeError, TypeError):
                        continue  # boot logs or malformed frames
                    db.insert(frame)
        except (serial.SerialException, OSError):
            LOG.warning("Serial unavailable: %s; retrying in 3 seconds", port)
        except Exception:
            LOG.exception("Reader error; retrying in 3 seconds")
        finally:
            connected.clear()
        stop.wait(3)

def main():
    parser = argparse.ArgumentParser(description="ESP32 temperature database dashboard")
    parser.add_argument("--port", help="Actual ESP32 COM port; omit for history-only mode")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--backend", choices=["sqlite","mariadb"], default="sqlite")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--http-port", type=int, default=5000)
    parser.add_argument("--open-browser", action="store_true", help="Open local dashboard once the server responds")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if args.backend == 'mariadb':
        from mariadb_database import MariaDatabase
        db = MariaDatabase()
    else:
        db = Database(args.db)
    connected, stop = threading.Event(), threading.Event()
    thread = None
    if args.port:
        thread = threading.Thread(target=read_serial, args=(args.port, db, connected, stop), daemon=True)
        thread.start()
    else:
        LOG.info("History-only mode; no serial port selected.")
    if args.open_browser:
        def open_dashboard():
            url = f'http://127.0.0.1:{args.http_port}/'
            for _ in range(40):
                if stop.is_set(): return
                try:
                    with urllib.request.urlopen(url, timeout=1) as response:
                        if response.status == 200:
                            webbrowser.open(url)
                            return
                except OSError:
                    stop.wait(0.5)
        threading.Thread(target=open_dashboard, daemon=True).start()
    try:
        create_app(db, connected).run(host=args.host, port=args.http_port, debug=False, use_reloader=False)
    finally:
        stop.set()
        if thread:
            thread.join(timeout=4)

if __name__ == "__main__":
    main()
