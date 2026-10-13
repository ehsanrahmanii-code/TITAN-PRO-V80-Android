#!/usr/bin/env python3
"""Assemble TITAN V80 engine from embedded base64 parts into Chaquopy python path."""
from __future__ import annotations
import base64, shutil, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_DST = ROOT / "app" / "src" / "main" / "python"
PARTS_PKG = ROOT / "scripts" / "engine_parts"

def main():
    parts = []
    for i in range(100):
        mod_path = PARTS_PKG / f"engine_part_{i:02d}.py"
        if not mod_path.is_file():
            break
        ns = {}
        exec(mod_path.read_text(encoding="utf-8"), ns)
        parts.append(ns["PART"])
    if not parts:
        raise SystemExit("no engine parts found")
    data = base64.b64decode("".join(parts))
    zip_path = ROOT / "TITAN_PRO_V80_FINAL.zip"
    zip_path.write_bytes(data)
    print(f"zip_bytes={len(data)}")
    tmp = ROOT / "_titan_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(tmp)
    src = tmp / "titan_pro" / "titan"
    if not src.is_dir():
        cand = list(tmp.rglob("runtime.py"))
        if not cand:
            raise SystemExit("runtime.py not found")
        src = cand[0].parent
    dst = PY_DST / "titan"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    run = tmp / "titan_pro" / "run_titan.py"
    if run.exists():
        shutil.copy2(run, PY_DST / "run_titan.py")
    print(f"installed_titan_to={dst}")
    print(f"py_files={sum(1 for _ in dst.rglob('*.py'))}")

if __name__ == "__main__":
    main()
