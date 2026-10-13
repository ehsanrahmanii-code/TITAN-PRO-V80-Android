#!/usr/bin/env python3
"""Assemble TITAN_PRO_V80_FINAL.zip from base64 parts and extract into Chaquopy python path.
If parts are incomplete/missing, keep any already-present titan package (do not wipe).
"""
from __future__ import annotations

import base64
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "engine_full_b64"
OUT_ZIP = ROOT / "TITAN_PRO_V80_FINAL.zip"
PY_DST = ROOT / "app" / "src" / "main" / "python"


def main() -> None:
    parts = sorted(PARTS.glob("p*.b64"))
    if not parts:
        print(f"WARN: no parts in {PARTS} — keeping existing python/titan if any")
        dst = PY_DST / "titan"
        if dst.is_dir():
            n = sum(1 for _ in dst.rglob("*.py"))
            print(f"existing_titan_py_files={n}")
        return

    try:
        data = b"".join(base64.b64decode(p.read_text().strip()) for p in parts)
    except Exception as e:
        print(f"WARN: b64 decode failed: {e} — keeping existing titan")
        return

    print(f"zip_bytes={len(data)}")
    if len(data) < 10000:
        print("WARN: assembled zip too small — keeping existing titan")
        return

    OUT_ZIP.write_bytes(data)
    tmp = ROOT / "_titan_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    try:
        with zipfile.ZipFile(OUT_ZIP) as zf:
            zf.extractall(tmp)
    except Exception as e:
        print(f"WARN: zip extract failed: {e} — keeping existing titan")
        return

    src = tmp / "titan_pro" / "titan"
    if not src.is_dir():
        cand = list(tmp.rglob("runtime.py"))
        if not cand:
            print("WARN: runtime.py not found in zip — keeping existing titan")
            return
        src = cand[0].parent

    dst = PY_DST / "titan"
    # Only replace if the extracted package looks complete (many layers)
    py_count = sum(1 for _ in src.rglob("*.py"))
    print(f"extracted_py_files={py_count}")
    if py_count < 50:
        print("WARN: extracted package incomplete — keeping existing titan")
        return

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
