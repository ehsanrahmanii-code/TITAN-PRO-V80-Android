#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/engine_b64"
OUT="$ROOT/app/src/main/assets/TITAN_PRO_V80_FINAL.zip"
mkdir -p "$(dirname "$OUT")"
if ls "$SRC"/p*.b64 >/dev/null 2>&1; then
  cat "$SRC"/p*.b64 | tr -d '\n\r ' | base64 -d > "$OUT"
  ls -lh "$OUT"
  python3 -c "import zipfile; z=zipfile.ZipFile(r'$OUT'); assert z.testzip() is None; print('zip_ok', len(z.namelist()), 'files')"
else
  echo "No engine_b64 parts found" >&2
  exit 1
fi
