# -*- coding: utf-8 -*-
"""Bootstrap TITAN PRO V80 — same pattern as working V75 Full Android."""
from __future__ import annotations

import os
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path

_started = False
_lock = threading.Lock()
_last_error = ""
_error_log = None
_status = {"ok": False, "msg": "not started", "engine": "none", "version": "80.0.0"}

HOST = "127.0.0.1"
PORT = 8080


def _record_error(label: str) -> str:
    global _last_error
    details = traceback.format_exc()
    _last_error = f"{label}:\n{details}"
    try:
        if _error_log is not None:
            _error_log.parent.mkdir(parents=True, exist_ok=True)
            with _error_log.open("a", encoding="utf-8") as fp:
                fp.write("\n" + "=" * 70 + "\n" + _last_error + "\n")
    except Exception:
        pass
    print(_last_error, flush=True)
    return _last_error


def start_server(files_dir: str | None = None) -> str:
    """Alias used by current MainActivity."""
    return start_titan(files_dir or ".")


def start_titan(files_dir: str) -> str:
    """Start the real TITAN Flask engine. Same contract as V75."""
    global _started, _last_error, _error_log, _status
    with _lock:
        if _started:
            return "already_started"
        try:
            home = Path(files_dir) / "MMM"
            _error_log = home / "logs" / "android_engine_error.log"
            for sub in (
                home,
                home / "data",
                home / "cache",
                home / "memory",
                home / "secrets",
                home / "logs",
                home / "cache" / "tmp",
            ):
                sub.mkdir(parents=True, exist_ok=True)

            os.environ["TITAN_MMM"] = str(home)
            os.environ["TITAN_HOME"] = str(home)
            os.environ["TITAN_FILES_DIR"] = str(files_dir)
            os.environ["TITAN_OPEN_BROWSER"] = "0"
            os.environ["TITAN_HOST"] = HOST
            os.environ["TITAN_PORT"] = str(PORT)
            os.environ["TITAN_PORT_DEFAULT"] = str(PORT)
            os.environ["TMPDIR"] = str(home / "cache" / "tmp")
            os.environ["TEMP"] = str(home / "cache" / "tmp")
            os.environ["TMP"] = str(home / "cache" / "tmp")
            os.environ["PYTHONUNBUFFERED"] = "1"
            os.environ.setdefault("HOME", str(files_dir))

            import titan.runtime as rt
            ns = rt.load(__file__, as_main=False, stop_before="entry/main_entry")
            _status["engine"] = "titan_full_v80"
            _status["layers_log"] = ns.get("_TITAN_LAYER_LOG", [])
            run_titan = ns.get("run_titan")
            app = ns.get("app")

            def _run():
                try:
                    if callable(run_titan):
                        try:
                            run_titan(open_browser=False)
                        except TypeError:
                            run_titan()
                    elif app is not None:
                        try:
                            from waitress import serve
                            serve(app, host=HOST, port=PORT, threads=6)
                        except Exception:
                            app.run(host=HOST, port=PORT, threaded=True, use_reloader=False)
                    else:
                        from flask import Flask
                        fb = Flask(__name__)

                        @fb.route("/")
                        def idx():
                            loaded = [x.get("layer") for x in (ns.get("_TITAN_LAYER_LOG") or []) if not x.get("skipped")]
                            skipped = [x.get("layer") for x in (ns.get("_TITAN_LAYER_LOG") or []) if x.get("skipped")]
                            return (
                                "<!doctype html><html lang=fa dir=rtl><meta charset=utf-8>"
                                "<body style='background:#050812;color:#e2e8f0;font-family:Tahoma;padding:24px'>"
                                "<h1 style='color:#38bdf8'>⚡ TITAN PRO V80</h1>"
                                f"<p>لایه‌های لود شده: {len(loaded)}</p>"
                                f"<p style='color:#f87171'>لایه‌های جاافتاده: {len(skipped)}</p>"
                                "<p>موتور کامل هنوز embed نشده. در حال تکمیل…</p></body></html>"
                            ), 200, {"Content-Type": "text/html; charset=utf-8"}

                        @fb.route("/health")
                        def h():
                            import json
                            return json.dumps(_status, ensure_ascii=False), 200, {"Content-Type": "application/json"}

                        try:
                            from waitress import serve
                            serve(fb, host=HOST, port=PORT, threads=4)
                        except Exception:
                            fb.run(host=HOST, port=PORT, threaded=True, use_reloader=False)
                except Exception:
                    _record_error("TITAN run_titan error")

            threading.Thread(target=_run, name="titan-flask", daemon=True).start()
            _started = True
            _status["ok"] = True
            _status["msg"] = "started"
            return "started"
        except Exception as exc:
            _record_error("TITAN bootstrap error")
            _status["ok"] = False
            _status["msg"] = _last_error[:500]
            try:
                from flask import Flask
                fb = Flask(__name__)
                err = _last_error

                @fb.route("/")
                def idx():
                    return (
                        f"<!doctype html><html lang=fa dir=rtl><meta charset=utf-8>"
                        f"<body style='background:#050812;color:#e2e8f0;font-family:Tahoma;padding:24px'>"
                        f"<h1 style='color:#f87171'>خطای موتور</h1><pre>{err[:2000]}</pre></body></html>"
                    ), 200, {"Content-Type": "text/html; charset=utf-8"}

                @fb.route("/health")
                def h():
                    return '{"ok":false}', 200, {"Content-Type": "application/json"}

                def _fb():
                    try:
                        from waitress import serve
                        serve(fb, host=HOST, port=PORT, threads=2)
                    except Exception:
                        fb.run(host=HOST, port=PORT, threaded=True, use_reloader=False)

                threading.Thread(target=_fb, daemon=True).start()
                _started = True
            except Exception:
                pass
            return f"error:{_last_error[:300]}"


def wait_ready(url: str = "http://127.0.0.1:8080/health", timeout: float = 180.0) -> bool:
    deadline = time.time() + float(timeout)
    urls = [
        url,
        f"http://{HOST}:{PORT}/",
        f"http://{HOST}:{PORT}/health",
        f"http://localhost:{PORT}/health",
        f"http://localhost:{PORT}/",
    ]
    while time.time() < deadline:
        for u in urls:
            try:
                with urllib.request.urlopen(u, timeout=2.5) as resp:
                    if 200 <= getattr(resp, "status", 200) < 500:
                        return True
            except Exception:
                pass
        time.sleep(1.0)
    return False


def last_error() -> str:
    return _last_error or ""


def health() -> str:
    import json
    return json.dumps(_status, ensure_ascii=False)
