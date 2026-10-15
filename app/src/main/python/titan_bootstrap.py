# -*- coding: utf-8 -*-
"""Bootstrap TITAN PRO V80 — load engine already packaged by Chaquopy."""
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


def _load_engine():
    """Load titan.runtime from Chaquopy-packaged python/titan/."""
    # Prefer normal package import (Chaquopy puts app/src/main/python on path)
    try:
        from titan import runtime as mod
    except Exception:
        # Fallback: load by file path next to this module
        import importlib.util
        here = Path(__file__).resolve().parent
        rt_path = here / "titan" / "runtime.py"
        if not rt_path.is_file():
            raise FileNotFoundError(f"runtime.py not packaged: {rt_path}")
        spec = importlib.util.spec_from_file_location("titan.runtime", str(rt_path))
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load runtime")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["titan.runtime"] = mod
        spec.loader.exec_module(mod)

    # Chaquopy AssetFinder paths are virtual: pathlib may report that the
    # packaged "titan/layers" directory does not exist even though its Python
    # modules are available to the import loader. Validate via import machinery.
    import importlib.util
    layer_dir = Path(mod.__file__).resolve().parent / "layers"
    mod.LAYER_DIR = layer_dir
    try:
        bs_spec = importlib.util.find_spec("titan.layers.core.bootstrap_storage")
    except (ImportError, ModuleNotFoundError, ValueError):
        bs_spec = None
    if bs_spec is None or bs_spec.loader is None:
        raise FileNotFoundError(
            "Packaged TITAN layer module unavailable: "
            "titan.layers.core.bootstrap_storage; "
            f"runtime={mod.__file__}; layer_path={layer_dir}"
        )

    ns = mod.load(str(Path(mod.__file__).resolve()), as_main=False, stop_before="entry/main_entry")
    return ns


def start_server(files_dir: str | None = None) -> str:
    return start_titan(files_dir or ".")


def start_titan(files_dir: str) -> str:
    global _started, _last_error, _error_log, _status
    with _lock:
        if _started:
            return "already_started"
        try:
            base = Path(files_dir)
            mmm = base / "MMM"
            _error_log = mmm / "logs" / "android_engine_error.log"
            for sub in (
                mmm,
                mmm / "data",
                mmm / "cache",
                mmm / "memory",
                mmm / "secrets",
                mmm / "logs",
                mmm / "cache" / "tmp",
            ):
                sub.mkdir(parents=True, exist_ok=True)

            os.environ["TITAN_MMM"] = str(mmm)
            os.environ["TITAN_HOME"] = str(mmm)
            os.environ["TITAN_FILES_DIR"] = str(files_dir)
            os.environ["TITAN_OPEN_BROWSER"] = "0"
            os.environ["TITAN_HOST"] = HOST
            os.environ["TITAN_PORT"] = str(PORT)
            os.environ["TITAN_PORT_DEFAULT"] = str(PORT)
            os.environ["TMPDIR"] = str(mmm / "cache" / "tmp")
            os.environ["PYTHONUNBUFFERED"] = "1"
            os.environ.setdefault("HOME", str(files_dir))

            ns = _load_engine()
            _status["engine"] = "titan_full_v80"
            _status["layers_log"] = ns.get("_TITAN_LAYER_LOG", [])
            loaded = [x for x in (_status["layers_log"] or []) if not x.get("skipped")]
            _status["loaded"] = len(loaded)
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
                        raise RuntimeError("no run_titan or app after full load")
                except Exception:
                    _record_error("TITAN run_titan error")

            threading.Thread(target=_run, name="titan-flask", daemon=True).start()
            _started = True
            _status["ok"] = True
            _status["msg"] = f"started layers={len(loaded)}"
            return f"started:layers={len(loaded)}"
        except Exception:
            _record_error("TITAN bootstrap error")
            _status["ok"] = False
            _status["msg"] = _last_error[:800]
            try:
                from flask import Flask

                fb = Flask(__name__)
                err = _last_error

                @fb.route("/")
                def idx():
                    return (
                        f"<!doctype html><html lang=fa dir=rtl><meta charset=utf-8>"
                        f"<body style='background:#050812;color:#e2e8f0;font-family:Tahoma;padding:24px'>"
                        f"<h1 style='color:#f87171'>خطای موتور</h1>"
                        f"<pre style='white-space:pre-wrap;font-size:12px'>{err[:3500]}</pre></body></html>"
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
    urls = [url, f"http://{HOST}:{PORT}/", f"http://{HOST}:{PORT}/health"]
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
