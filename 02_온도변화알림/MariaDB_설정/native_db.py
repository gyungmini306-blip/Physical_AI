"""Native per-user MariaDB for the temperature assignment; no service or Docker."""
import argparse
import json
import os
import secrets
import subprocess
import time
from pathlib import Path

import pymysql

ROOT = Path(os.environ["LOCALAPPDATA"]) / "ESP32SchoolKit"
BIN = ROOT / "apps" / "mariadb-11.4.14-winx64" / "bin"
HOME = ROOT / "temperature-mariadb"
DATA = HOME / "data"
CONFIG = HOME / "credentials.json"
PORT = 3307
DB = "temperature_alert"
USER = "temperature_app"
SCHEMA = Path(__file__).resolve().parent / "init" / "01-schema.sql"

def settings():
    return json.loads(CONFIG.read_text(encoding="utf-8"))

def connection(root=False, database=True):
    cfg = settings()
    return pymysql.connect(host="127.0.0.1", port=PORT, user="root" if root else USER,
        password=cfg["root_password" if root else "app_password"],
        database=DB if database else None, charset="utf8mb4",
        connect_timeout=3, read_timeout=5, write_timeout=5, autocommit=True)

def verify(c):
    with c.cursor() as cur:
        cur.execute("SELECT @@datadir")
        found = Path(cur.fetchone()[0]).resolve()
    if os.path.normcase(str(found)) != os.path.normcase(str(DATA.resolve())):
        raise RuntimeError("Port 3307 belongs to a different MariaDB instance; no changes made.")

def root_ready():
    try:
        c = connection(root=True, database=False)
    except pymysql.MySQLError:
        return False
    try:
        verify(c)
        return True
    finally:
        c.close()

def start():
    if not (BIN / "mariadbd.exe").is_file():
        raise RuntimeError("Run 00 common setup first.")
    HOME.mkdir(parents=True, exist_ok=True)
    if not CONFIG.exists():
        if DATA.exists() and any(DATA.iterdir()):
            raise RuntimeError("Existing DB without credentials; recover credentials before continuing.")
        CONFIG.write_text(json.dumps({"root_password":secrets.token_hex(24),
            "app_password":secrets.token_hex(24)}), encoding="utf-8")
    cfg = settings()
    if not (DATA / "mysql").is_dir():
        if DATA.exists() and any(DATA.iterdir()):
            raise RuntimeError("Partial database initialization; inspect data and logs, do not delete automatically.")
        init = next((BIN / x for x in ("mariadb-install-db.exe","mysql_install_db.exe","mariadbd-install-db.exe")
                     if (BIN / x).is_file()), None)
        if init is None:
            raise RuntimeError("MariaDB Windows initialization executable not found.")
        subprocess.run([str(init), "--datadir="+str(DATA), "--port="+str(PORT),
                        "--password="+cfg["root_password"]], cwd=BIN, check=True)
    if not root_ready():
        import socket
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                raise RuntimeError("Port 3307 is already in use or credentials do not match.")
        log = HOME / "server.log"
        with log.open("ab") as out:
            proc = subprocess.Popen([str(BIN / "mariadbd.exe"), "--no-defaults",
                "--basedir="+str(BIN.parent), "--datadir="+str(DATA),
                "--port="+str(PORT), "--bind-address=127.0.0.1",
                "--character-set-server=utf8mb4", "--console"],
                cwd=BIN, stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
        for _ in range(40):
            if root_ready(): break
            if proc.poll() is not None: raise RuntimeError("MariaDB exited; see "+str(log))
            time.sleep(1)
        else: raise RuntimeError("MariaDB startup timed out; see "+str(log))
    c = connection(root=True, database=False)
    try:
        verify(c)
        with c.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS temperature_alert CHARACTER SET utf8mb4")
            for host in ("localhost", "127.0.0.1"):
                # Host is a constant from this tuple, password is parameterized.
                cur.execute("CREATE USER IF NOT EXISTS 'temperature_app'@'"+host+"' IDENTIFIED BY %s", (cfg["app_password"],))
                cur.execute("GRANT SELECT, INSERT ON temperature_alert.* TO 'temperature_app'@'"+host+"'")
            for statement in SCHEMA.read_text(encoding="utf-8").split(";"):
                if statement.strip(): cur.execute(statement)
    finally: c.close()
    check()

def check():
    c = connection()
    try:
        verify(c)
        with c.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM measurements")
            print("MariaDB connected. Saved rows:", cur.fetchone()[0])
    finally: c.close()

def stop():
    c = connection(root=True, database=False)
    try:
        verify(c)
        with c.cursor() as cur: cur.execute("SHUTDOWN")
    finally: c.close()
    print("MariaDB stopped. Data retained.")

def console():
    check()
    print("Application password is app_password in", CONFIG)
    subprocess.run([str(BIN / "mariadb.exe"), "--no-defaults", "-h", "127.0.0.1",
                    "-P", str(PORT), "-u", USER, "-p", DB], check=True)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action", choices=["start","check","stop","console"])
    args=parser.parse_args()
    try: globals()[args.action]()
    except Exception as exc:
        print("ERROR:", exc)
        raise SystemExit(1)
