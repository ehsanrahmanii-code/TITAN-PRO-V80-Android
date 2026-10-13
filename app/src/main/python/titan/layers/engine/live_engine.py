# [TITAN V77 layer] engine/live_engine - Live engine
# Original V76 source lines 7236-7325 (kept verbatim unless listed in CHANGELOG.md).
# ============================================================
# LIVE ENGINE
# ============================================================


def _register_live_price(symbol: str, price: float, source: str = "REST") -> None:
    if price <= 0: return
    symbol = _normalize_symbol(symbol)
    with LIVE_LOCK:
        previous = LIVE_PRICES.get(symbol, {})
        ch_24 = None
        try:
            t24 = (get_24h_tickers_cached([symbol]) or {}).get(symbol) or {}
            if t24 and math.isfinite(safe_float(t24.get("change_pct_24h"), float("nan"))):
                ch_24 = float(t24["change_pct_24h"])
        except Exception:
            _swallow()
        if ch_24 is None:
            ch_24 = ((price / previous["price"] - 1) * 100) if previous.get("price") else float(previous.get("change_pct") or 0.0)
        LIVE_PRICES[symbol] = {
            "price": float(price), "source": source, "ts": time.time(), "age_ms": 0,
            "change_pct": float(ch_24),
            "change_pct_24h": float(ch_24),
        }


def _live_status() -> dict[str, Any]:
    now = time.time()
    with LIVE_LOCK:
        rows = dict(LIVE_PRICES)
    if not rows:
        return {"status": "NO_DATA", "count": 0, "median_age_ms": None, "sources": [], "websocket": bool(_websocket_client)}
    ages = []; sources = set()
    for item in rows.values():
        age = max(0, now - float(item.get("ts", now))) * 1000; item["age_ms"] = round(age, 1); ages.append(age); sources.add(item.get("source", "REST"))
    median_age = statistics.median(ages) if ages else None
    return {"status": "LIVE" if median_age is not None and median_age < 10000 else "DELAYED", "count": len(rows), "median_age_ms": round(median_age, 1) if median_age is not None else None, "sources": sorted(sources), "websocket": bool(_websocket_client)}


def _rest_live_price_worker() -> None:
    _tick = 0
    while not LIVE_STOP.is_set():
        try:
            coins = USER_SETTINGS.get("active_coins") or DEFAULT_COINS
            if _tick % 8 == 0:
                try:
                    get_24h_tickers_cached(list(coins))
                except Exception:
                    _swallow()
            for symbol, price in _fetch_live_prices(coins).items():
                _register_live_price(symbol, price, "REST")
        except Exception as exc:
            LOGGER.warning("Live REST worker failed: %s", exc)
        _tick += 1
        LIVE_STOP.wait(LIVE_PRICE_POLL_SECONDS)


def _websocket_worker() -> None:
    if _websocket_client is None: return
    while not LIVE_STOP.is_set():
        try:
            symbols = [_normalize_symbol_for_binance(s).lower() for s in (USER_SETTINGS.get("active_coins") or DEFAULT_COINS)]
            streams = "/".join(f"{s}@miniTicker" for s in symbols)
            ws = _websocket_client.create_connection(f"wss://data-stream.binance.vision/stream?streams={streams}", timeout=10)
            ws.settimeout(10)
            while not LIVE_STOP.is_set():
                raw = ws.recv()
                if not raw: break
                data = json.loads(raw).get("data", {})
                symbol = str(data.get("s", "")); price = safe_float(data.get("c"), 0)
                if symbol and price > 0: _register_live_price(symbol, price, "WebSocket")
            try: ws.close()
            except Exception: _swallow()
        except Exception as exc:
            LOGGER.info("WebSocket unavailable; REST fallback active: %s", exc); LIVE_STOP.wait(5)


def start_live_engine() -> None:
    if any(t.is_alive() for t in LIVE_THREADS): return
    LIVE_STOP.clear()
    rest = threading.Thread(target=_rest_live_price_worker, name="titan-live-rest", daemon=True)
    rest.start(); LIVE_THREADS.append(rest)
    if _websocket_client is not None:
        ws = threading.Thread(target=_websocket_worker, name="titan-live-ws", daemon=True)
        ws.start(); LIVE_THREADS.append(ws)
        depth_t = threading.Thread(target=_depth_websocket_worker, name="titan-depth-ws", daemon=True)
        depth_t.start(); LIVE_THREADS.append(depth_t)
