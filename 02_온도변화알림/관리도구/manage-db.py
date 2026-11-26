"""Forward maintenance actions to the unchanged native MariaDB script."""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    script = Path(__file__).resolve().parent.parent / "MariaDB_설정" / "native_db.py"
    raise SystemExit(subprocess.call([sys.executable, str(script), *sys.argv[1:]]))
