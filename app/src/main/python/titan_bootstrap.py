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


def _start_error_server(err_msg: str, trace: str = ""):
    """Always start an HTTP server so WebView never gets CONNECTION_REFUSED."""
    try:
        from flask import Flask
        app = Flask(__name__)

        @app.route("/")
        def index():
            html = f"""<!doctype html>
<html lang=\"fa\" dir=\"rtl\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>TITAN PRO V80</title>
<style>
body{{background:#050812;color:#e2e8f0;font-family:Tahoma,sans-serif;padding:24px;margin:0}}
h1{{color:#38bdf8;font-size:1.4rem}}
.box{{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;margin:16px 0;word-break:break-all}}
.err{{color:#f87171}}
.ok{{color:#4ade80}}
pre{{white-space:pre-wrap;font-size:0.75rem;color:#94a3b8}}
</style>
</head>
<body>
<h1>⚡ TITAN PRO V80</h1>
<p>موتور در حال آماده‌سازی است یا لایه‌ها کامل نیستند.</p>
<div class=\"box\">
<p class=\"err\"><b>خطا:</b> {err_msg[:800].replace(\"<\",\"<\")}</p>
</div>
<p>بعد از به‌روزرسانی کامل لایه‌ها، این صفحه به داشبورد شیشه‌ای واقعی تبدیل می‌شود.</p>
<pre>{trace[-1500:].replace(\"<\",\"<\") if trace else \"\"}</pre>
</body></html>"""
            return html, 200, {"Content-Type": "text/html; charset=utf-8"}

        @app.route("/health")
        def health_route():
            import json
            return json.dumps(_status, ensure_ascii=False), 200, {"Content-Type": "application/json"}

        def _run():
            try:
                from waitress import serve
                serve(app, host=_HOST, port=_PORT, threads=4)
            except Exception:
                app.run(host=_HOST, port=_PORT, threaded=True, use_reloader=False)

        t = threading.Thread(target=_run, name="titan-error", daemon=True)
        t.start()
        return True
    except Exception as e:
        _status["msg"] = f"even_error_server_failed:{e}"
        return False


def start_server(files_dir: str | None = None) -> str:
    """Called from Kotlin. Starts REAL TITAN HTTP + glass dashboard, or error page."""
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
                    _start_error_server(str(e), _status.get("trace", ""))

            t = threading.Thread(target=_serve, name="titan-full", daemon=True)
            t.start()
            for _ in range(120):
                if _port_open(_HOST, _PORT):
                    break
                time.sleep(0.25)
            _started = True
            return f"started_full:{_HOST}:{_PORT}:mmm={mmm}"
        except Exception as e:
            _status["ok"] = False
            _status["engine"] = "load_failed"
            _status["msg"] = repr(e)
            _status["trace"] = traceback.format_exc()[-4000:]
            # CRITICAL: still start HTTP so WebView does not show CONNECTION_REFUSED
            _start_error_server(str(e), _status["trace"])
            for _ in range(40):
                if _port_open(_HOST, _PORT):
                    break
                time.sleep(0.2)
            _started = True
            return f"load_failed_but_error_page_up:{e}"


def health() -> str:
    import json
    return json.dumps(_status, ensure_ascii=False)
