# -*- coding: utf-8 -*-
"""Bootstrap TITAN PRO V80 — extract full engine zip from filesDir, then start Flask."""
from __future__ import annotations

import os
import shutil
import sys
import threading
import time
import traceback
import urllib.request
import zipfile
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


def _extract_engine(files_dir: str) -> Path:
    home = Path(files_dir)
    eng = home / "titan_engine"
    marker = eng / ".v80_ok"
    if marker.is_file() and (eng / "titan" / "runtime.py").is_file():
        n_layers = (eng / "titan" / "layers")
        if n_layers.is_dir() and any(n_layers.rglob("*.py")):
            return eng

    zip_path = home / "TITAN_PRO_V80_FINAL.zip"
    if not zip_path.is_file() or zip_path.stat().st_size < 100000:
        # try next to this module (if packaged as python data)
        alt = Path(__file__).resolve().parent / "TITAN_PRO_V80_FINAL.zip"
        if alt.is_file() and alt.stat().st_size > 100000:
            zip_path = alt
        else:
            raise FileNotFoundError(
                f"Engine zip missing or too small: {zip_path}. "
                "MainActivity must copy assets/TITAN_PRO_V80_FINAL.zip to filesDir."
            )

    if eng.exists():
        shutil.rmtree(eng)
    eng.mkdir(parents=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(eng)

    src = eng / "titan_pro" / "titan"
    if not src.is_dir():
        found = list(eng.rglob("runtime.py"))
        if not found:
            raise FileNotFoundError("runtime.py missing after extract")
        src = found[0].parent

    dest = eng / "titan"
    if src.resolve() != dest.resolve():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)

    n = sum(1 for _ in (eng / "titan").rglob("*.py"))
    if n < 50:
        raise RuntimeError(f"too few engine files after extract: {n}")
    marker.write_text(f"py_files={n}\n", encoding="utf-8")
    print(f"TITAN engine extracted: {n} py files -> {eng}", flush=True)
    return eng


def _load_from_engine(eng: Path):
    titan_dir = eng / "titan"
    if str(eng) not in sys.path:
        sys.path.insert(0, str(eng))

    import importlib.util
    rt_path = titan_dir / "runtime.py"
    if not rt_path.is_file():
        raise FileNotFoundError(f"runtime missing at {rt_path}")

    spec = importlib.util.spec_from_file_location("titan_runtime_v80", str(rt_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load runtime spec")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["titan_runtime_v80"] = mod
    sys.modules["titan.runtime"] = mod
    spec.loader.exec_module(mod)

    # Force LAYER_DIR to extracted path so all layers resolve
    mod.LAYER_DIR = titan_dir / "layers"
    if not mod.LAYER_DIR.is_dir():
        raise FileNotFoundError(f"layers dir missing: {mod.LAYER_DIR}")

    # Verify bootstrap_storage exists before load
    bs = mod.LAYER_DIR / "core" / "bootstrap_storage.py"
    if not bs.is_file():
        raise FileNotFoundError(f"bootstrap_storage missing: {bs}")

    ns = mod.load(str(rt_path), as_main=False, stop_before="entry/main_entry")
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
            for sub in (mmm, mmm / "data", mmm / "cache", mmm / "memory", mmm / "secrets", mmm / "logs", mmm / "cache" / "tmp"):
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

            eng = _extract_engine(files_dir)
            ns = _load_from_engine(eng)
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
