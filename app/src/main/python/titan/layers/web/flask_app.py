# [TITAN V77 layer] web/flask_app - Flask app
# Original V76 source lines 8391-8462 (kept verbatim unless listed in CHANGELOG.md).
# ============================================================
# FLASK
# ============================================================


app = Flask(__name__, instance_path=str(FLASK_INSTANCE_DIR))
app.config["JSON_AS_ASCII"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = False
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600
# Android-safe default: local-only dashboard.
HOST = os.environ.get("TITAN_HOST", "127.0.0.1")
_default_port = os.environ.get("TITAN_PORT_DEFAULT") or "8080"
try:
    PORT = int(os.environ.get("TITAN_PORT", _default_port) or _default_port)
except (TypeError, ValueError):
    PORT = int(_default_port)

@app.get("/favicon.ico")
def titan_favicon():
    return "", 204

@app.errorhandler(404)
def titan_not_found(exc):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "not_found"}), 404
    return ("<h1>TITAN: 404</h1>", 404, {"Content-Type": "text/html; charset=utf-8"})

@app.errorhandler(Exception)
def titan_global_error_handler(exc):
    # Keep API responses JSON, but never leave the human-facing dashboard blank.
    # Production-safe: do not leak full exception text to the browser unless TITAN_DEBUG=1.
    LOGGER.exception("Unhandled application error: %s", exc)
    debug = str(os.environ.get("TITAN_DEBUG", "")).lower() in {"1", "true", "yes"}
    if request.path.startswith("/api/"):
        body = {"ok": False, "error": "internal_error"}
        if debug:
            body["detail"] = str(exc)[:500]
        return jsonify(body), 500
    detail_html = (
        str(exc).replace("<", "<").replace(">", ">").replace("\n", "<br>")
        if debug else "جزئیات فقط در حالت TITAN_DEBUG=1 نمایش داده می‌شود. لاگ سرور را بررسی کنید."
    )
    return (
        "<!doctype html><html lang='fa' dir='rtl'><meta charset='utf-8'>"
        "<title>TITAN Enterprise Error</title>"
        "<body style='background:#050812;color:#eef2ff;font-family:Tahoma;padding:30px'>"
        "<h2 style='color:#38bdf8'>⚡ TITAN ENTERPRISE</h2>"
        "<p>داشبورد با یک خطای داخلی مواجه شد، اما سرور فعال است.</p>"
        f"<pre style='white-space:pre-wrap;background:#0b1220;padding:16px;border-radius:12px'>{detail_html}</pre>"
        "<p>بعد از رفع خطا صفحه را Refresh کنید.</p></body></html>", 500, {"Content-Type": "text/html; charset=utf-8"}
    )

def _gemini_dashboard_status(summary: str) -> dict[str, Any]:
    return {
        "available": bool(GEMINI_API_KEY),
        "ready": bool(summary.strip()),
        "label": "تحلیل آماده" if summary.strip() else ("کلید Gemini موجود نیست" if not GEMINI_API_KEY else "در انتظار تحلیل"),
        "updated_at": _now_iso(),
    }


def _as_map(value):
    """Jinja-safe: only treat real dict/mapping as map; strings/lists become {}."""
    try:
        from collections.abc import Mapping
        if isinstance(value, Mapping) and not isinstance(value, (str, bytes)):
            return dict(value)
    except Exception:
        _swallow()
    return {}

def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []
