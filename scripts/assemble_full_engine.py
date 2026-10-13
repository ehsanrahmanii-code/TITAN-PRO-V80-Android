#!/usr/bin/env python3
"""Assemble TITAN_PRO_V80_FINAL.zip from base64 parts and extract into Chaquopy python path."""
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
        raise SystemExit(f"no parts in {PARTS}")
    data = b"".join(base64.b64decode(p.read_text().strip()) for p in parts)
    OUT_ZIP.write_bytes(data)
    print(f"zip_bytes={len(data)}")
    tmp = ROOT / "_titan_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    with zipfile.ZipFile(OUT_ZIP) as zf:
        zf.extractall(tmp)
    src = tmp / "titan_pro" / "titan"
    if not src.is_dir():
        cand = list(tmp.rglob("runtime.py"))
        if not cand:
            raise SystemExit("runtime.py not found in zip")
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
