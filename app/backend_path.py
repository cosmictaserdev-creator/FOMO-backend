"""Makes backend/'s modules (config, db, collector, filter, ...) importable.

backend/ is a flat script layout (no [build-system], not an installable package), and
when frozen by PyInstaller it's bundled as plain source data rather than an installed
dependency. Importing this module before `import config` / `import db` elsewhere keeps
that one path-resolution concern in a single place.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


def backend_dir() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller onedir layout: backend/ is bundled alongside the exe.
        return Path(sys._MEIPASS) / "backend"  # type: ignore[attr-defined]
    return Path(__file__).parent.parent / "backend"


_BACKEND_DIR = backend_dir()
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# db.py calls a bare load_dotenv() which only searches upward from the current working
# directory -- that never finds backend/.env when this process's cwd is app/ (a sibling,
# not an ancestor). Load it explicitly by absolute path first; load_dotenv() doesn't
# override already-set os.environ values, so db.py's later call is a harmless no-op.
load_dotenv(_BACKEND_DIR / ".env")
