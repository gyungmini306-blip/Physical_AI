"""SQLite storage and validation for temperature telemetry."""
import csv
import io
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

STATES = {"WARMING_UP", "STABLE", "RISING", "FALLING", "SENSOR_ERROR"}

def decode(line):
    d = json.loads(line)
    if not isinstance(d, dict) or d.get("kind") != "temperature":
        raise ValueError("Not a temperature frame")
    if not isinstance(d.get("boot"), str) or not re.fullmatch("[0-9a-f]{16}", d["boot"]):
        raise ValueError("Invalid boot ID")
    for key in ("seq", "uptime_ms"):
        if type(d.get(key)) is not int or not 0 <= d[key] <= 4294967295:
            raise ValueError("Invalid counter")
    if d["seq"] == 0:
        raise ValueError("Invalid sequence")
    if not isinstance(d.get("state"), str) or d["state"] not in STATES or type(d.get("alarm")) is not bool:
        raise ValueError("Invalid state")
    for key in ("temperature", "delta"):
        if key not in d:
            raise ValueError("Missing measurement")
        v = d[key]
        if v is not None and (type(v) not in (int, float) or not -200 <= v <= 200 or not math.isfinite(v)):
            raise ValueError("Invalid measurement")
    if d["state"] == "SENSOR_ERROR":
        if d["temperature"] is not None or d["delta"] is not None:
            raise ValueError("Invalid error frame")
    elif d["temperature"] is None:
        raise ValueError("Missing temperature")
    if d["state"] == "WARMING_UP" and d["delta"] is not None:
        raise ValueError("Invalid warmup frame")
    if d["state"] in {"STABLE", "RISING", "FALLING"} and d["delta"] is None:
        raise ValueError("Missing delta")
    if d["alarm"] and d["state"] not in {"RISING", "FALLING"}:
        raise ValueError("Invalid alarm")
    return d

class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.executescript("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY,
                    received_at TEXT NOT NULL,
                    boot TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    uptime_ms INTEGER NOT NULL,
                    temperature REAL,
                    delta REAL,
                    state TEXT NOT NULL,
                    alarm INTEGER NOT NULL CHECK(alarm IN (0,1)),
                    UNIQUE(boot, seq)
                );
                CREATE INDEX IF NOT EXISTS idx_received ON measurements(received_at);
                CREATE INDEX IF NOT EXISTS idx_alarm ON measurements(alarm, id);
            """)

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()

    def insert(self, d):
        now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        with self.connect() as c:
            cur = c.execute("""
                INSERT INTO measurements
                    (received_at,boot,seq,uptime_ms,temperature,delta,state,alarm)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(boot,seq) DO NOTHING
            """, (now, d["boot"], d["seq"], d["uptime_ms"], d["temperature"],
                  d["delta"], d["state"], int(d["alarm"])))
            return cur.rowcount == 1

    def snapshot(self, start=None, end=None, limit=200):
        where, args = self.period(start, end)
        with self.connect() as c:
            c.execute("BEGIN")
            latest = c.execute("SELECT * FROM measurements ORDER BY id DESC LIMIT 1").fetchone()
            stats = c.execute("SELECT COUNT(*) AS samples, COUNT(temperature) AS valid, "
                "MIN(temperature) AS minimum, MAX(temperature) AS maximum, AVG(temperature) AS average, "
                "COALESCE(SUM(alarm),0) AS alarms FROM measurements" + where, args).fetchone()
            rows = c.execute("SELECT * FROM measurements" + where +
                " ORDER BY id DESC LIMIT ?", (*args, limit)).fetchall()
            alarms = c.execute("SELECT * FROM measurements" + where +
                (" AND " if where else " WHERE ") + "alarm=1 ORDER BY id DESC LIMIT 100", args).fetchall()
        return dict(latest=dict(latest) if latest else None, stats=dict(stats),
                    history=[dict(r) for r in reversed(rows)], alarms=[dict(r) for r in alarms])

    @staticmethod
    def period(start, end):
        clauses, args = [], []
        for value, op in ((start, ">="), (end, "<")):
            if value is not None:
                clauses.append("received_at " + op + " ?")
                args.append(value)
        return (" WHERE " + " AND ".join(clauses) if clauses else "", tuple(args))

    def export_csv(self, start=None, end=None):
        where, args = self.period(start, end)
        out = io.StringIO()
        writer = csv.writer(out)
        with self.connect() as c:
            cur = c.execute("SELECT * FROM measurements" + where + " ORDER BY id", args)
            writer.writerow([col[0] for col in cur.description])
            writer.writerows(cur)
        return out.getvalue()
