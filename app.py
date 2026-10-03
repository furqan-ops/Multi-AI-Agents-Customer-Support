import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DASHBOARD_DIR = ROOT / "project-3" / "dashboard"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

target_file = DASHBOARD_DIR / "app.py"
__file__ = str(target_file)

with open(target_file, "r", encoding="utf-8") as f:
    code = compile(f.read(), str(target_file), "exec")
    exec(code, globals())
