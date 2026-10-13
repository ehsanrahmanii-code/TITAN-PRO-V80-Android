# -*- coding: utf-8 -*-
"""Boot REAL TITAN PRO V80 inside the APK (Chaquopy). Not a demo shell."""
from __future__ import annotations

import os
import socket
import threading
import time
import traceback
from pathlib import Path

_HOST = "127.0.0.1"
_PORT = 8080
_started = False
_lock = threading.Lock()
_status = {"ok": False, "msg": "not started", "engine": "none", "version": "80.0.0"}


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except Exception:
        return False


def _setup_paths(files_dir: str | None) -> Path:
    base = Path(files_dir or os.environ.get("TITAN_FILES_DIR") or ".")
    mmm = base / "MMM"
    for sub in ("data", "cache", "memory", "secrets", "logs"):
        (mmm / sub).mkdir(parents=True, exist_ok=True)
    os.environ["TITAN_MMM"] = str(mmm)
    os.environ["TITAN_HOST"] = _HOST
    os.environ["TITAN_PORT"] = str(_PORT)
    os.environ["TITAN_OPEN_BROWSER"] = "0"
    os.environ["TITAN_DEBUG"] = "0"
    os.environ.setdefault("HOME", str(base))
    return mmm


def _load_full_engine():
    import titan.runtime as rt

    ns = rt.load(__file__, as_main=False, stop_before="entry/main_entry")
    return ns


def start_server(files_dir: str | None = None) -> str:
    """Called from Kotlin. Starts REAL TITAN HTTP + glass dashboard."""
    global _started
    with _lock:
        if files_dir:
            os.environ["TITAN_FILES_DIR"] = files_dir
        mmm = _setup_paths(files_dir)
        if _started or _port_open(_HOST, _PORT):
            _started = True
            return f"already_running:{_HOST}:{_PORT}"

        try:
            ns = _load_full_engine()
            _status["engine"] = "titan_full_v80"
            _status["ok"] = True
            _status["msg"] = "TITAN PRO V80 layers loaded"
            run_titan = ns.get("run_titan")
            app = ns.get("app")

            def _serve():
                try:
                    if callable(run_titan):
                        run_titan(open_browser=False)
                    elif app is not None:
                        try:
                            from waitress import serve

                            serve(app, host=_HOST, port=_PORT, threads=6)
                        except Exception:
                            app.run(host=_HOST, port=_PORT, threaded=True, use_reloader=False)
                    else:
                        raise RuntimeError("no run_titan or app in TITAN namespace")
                except Exception as e:
                    _status["ok"] = False
                    _status["msg"] = f"server_error:{e}"
                    _status["trace"] = traceback.format_exc()[-3000:]

            t = threading.Thread(target=_serve, name="titan-full", daemon=True)
            t.start()
            for _ in range(100):
                if _port_open(_HOST, _PORT):
                    break
                time.sleep(0.2)
            _started = True
            return f"started_full:{_HOST}:{_PORT}:mmm={mmm}"
        except Exception as e:
            _status["ok"] = False
            _status["engine"] = "load_failed"
            _status["msg"] = repr(e)
            _status["trace"] = traceback.format_exc()[-4000:]
            return f"load_failed:{e}"


def health() -> str:
    import json

    return json.dumps(_status, ensure_ascii=False)
