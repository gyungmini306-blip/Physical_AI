"""MariaDB backend implementing the existing dashboard storage interface."""
import csv
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import pymysql
from database import Database

CONFIG = Path(os.environ.get("LOCALAPPDATA", ".")) / "ESP32SchoolKit" / "temperature-mariadb" / "credentials.json"

class MariaDatabase:
    def __init__(self):
        self.password = json.loads(CONFIG.read_text(encoding="utf-8"))["app_password"]
        with self.connect() as c:
            with c.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM measurements")

    def connect(self):
        return pymysql.connect(host="127.0.0.1", port=3307, user="temperature_app",
            password=self.password, database="temperature_alert", charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor, connect_timeout=4,
            read_timeout=10, write_timeout=10, autocommit=True)

    def insert(self, d):
        with self.connect() as c:
            with c.cursor() as cur:
                try:
                    cur.execute("""INSERT INTO measurements
                        (received_at,boot,seq,uptime_ms,temperature,delta,state,alarm)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (datetime.now(timezone.utc).replace(tzinfo=None), d["boot"],d["seq"],
                         d["uptime_ms"],d["temperature"],d["delta"],d["state"],int(d["alarm"])))
                    return True
                except pymysql.err.IntegrityError as exc:
                    if exc.args[0] == 1062: return False
                    raise

    @staticmethod
    def period(start,end):
        where,args=Database.period(start,end)
        return where.replace("?", "%s"), tuple(datetime.fromisoformat(a).astimezone(timezone.utc).replace(tzinfo=None) for a in args)

    @staticmethod
    def row(r):
        if r is None: return None
        r=dict(r)
        r["received_at"]=r["received_at"].replace(tzinfo=timezone.utc).isoformat(timespec="milliseconds")
        return r

    def snapshot(self,start=None,end=None,limit=200):
        where,args=self.period(start,end)
        with self.connect() as c:
            c.begin()
            with c.cursor() as cur:
                cur.execute("SELECT * FROM measurements ORDER BY id DESC LIMIT 1")
                latest=self.row(cur.fetchone())
                cur.execute("SELECT COUNT(*) AS samples, COUNT(temperature) AS valid, MIN(temperature) AS minimum, MAX(temperature) AS maximum, AVG(temperature) AS average, COALESCE(SUM(alarm),0) AS alarms FROM measurements"+where,args)
                stats=cur.fetchone()
                stats["alarms"]=int(stats["alarms"])
                cur.execute("SELECT * FROM measurements"+where+" ORDER BY id DESC LIMIT %s",(*args,limit))
                history=[self.row(r) for r in reversed(cur.fetchall())]
                cur.execute("SELECT * FROM measurements"+where+(" AND " if where else " WHERE ")+"alarm=1 ORDER BY id DESC LIMIT 100",args)
                alarms=[self.row(r) for r in cur.fetchall()]
            c.commit()
        return dict(latest=latest,stats=stats,history=history,alarms=alarms)

    def export_csv(self,start=None,end=None):
        where,args=self.period(start,end)
        out=io.StringIO()
        with self.connect() as c:
            with c.cursor() as cur:
                cur.execute("SELECT * FROM measurements"+where+" ORDER BY id",args)
                names=[x[0] for x in cur.description]
                writer=csv.DictWriter(out,fieldnames=names)
                writer.writeheader()
                writer.writerows(self.row(r) for r in cur.fetchall())
        return out.getvalue()
