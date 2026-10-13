from __future__ import annotations

import hashlib
import copy
import json
import logging
import math
import os
import re
import sqlite3
import threading
import time
import traceback
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

# ============================================================
# TITAN V80 - core/bootstrap_storage
# MMM paths, atomic JSON/SQLite helpers, secrets, cache dirs
# ============================================================

LOGGER = logging.getLogger("titan.bootstrap_storage")

# Will be set by later layers / runtime
MMM: Path = Path(os.environ.get("TITAN_MMM", ".")) / "MMM" if False else Path(".")

def _ensure_mmm() -> Path:
    global MMM
    base = Path(os.environ.get("TITAN_MMM") or os.environ.get("TITAN_FILES_DIR") or ".")
    if (base / "MMM").exists() or os.environ.get("TITAN_MMM"):
        MMM = Path(os.environ.get("TITAN_MMM", str(base / "MMM")))
    else:
        MMM = base / "MMM"
    for sub in ("data", "cache", "memory", "secrets", "logs"):
        (MMM / sub).mkdir(parents=True, exist_ok=True)
    return MMM

def atomic_write_json(path: Path, data: Any, indent: int = 2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass
        raise

def safe_read_json(path: Path, default: Any = None) -> Any:
    path = Path(path)
    if not path.is_file():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _swallow(*_a, **_k):
    pass

# Minimal stubs so later layers that expect these names do not crash hard
def get_mmm() -> Path:
    return _ensure_mmm()

def ensure_dirs() -> Path:
    return _ensure_mmm()

_ensure_mmm()
