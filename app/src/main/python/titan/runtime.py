"""Layer loader for TITAN PRO V80.

The TITAN layers intentionally share one namespace because later layers wrap
functions created by earlier layers. Each source file is compiled with its real
path and executed in order, preserving the wrapper chain and useful tracebacks.
"""
from __future__ import annotations

import __future__ as _fut
import sys
import time
import types
from pathlib import Path

LAYER_ORDER = [
    "core/bootstrap_storage", "core/logging_safety_keys", "core/defaults_helpers",
    "core/confidence_v8", "data/storage_sqlite", "data/market_http",
    "decision/technicals_core", "decision/neural_synapse_v9",
    "decision/signal_grade_v10", "decision/decision_core_v3", "decision/ai_layer",
    "analysis/asset_analysis", "analysis/professional_edge_suite",
    "analysis/adaptive_intelligence", "engine/paper_forecast_metrics",
    "engine/backtest_walkforward", "engine/live_engine", "engine/cache_command_center",
    "engine/advanced_metrics", "engine/performance_snapshot",
    "engine/enterprise_audit_validation", "web/flask_app",
    "intel/v10_5_cognitive_nexus", "intel/v21_trust_max", "intel/v22_opportunity",
    "intel/v29_evidence_fusion", "intel/v30_deep_consensus", "intel/v31_canonical_decision",
    "intel/v32_performance_learning", "web/routes_startup",
    "governors/v29_3_central_governor", "governors/v29_5_edge_lab",
    "governors/v31_advanced_edge_suite", "governors/v34_adaptive_trust",
    "governors/v35_live_price_levels", "governors/v36_quantum_resonance",
    "governors/v40_five_hard_fixes", "governors/v42_integrity_seal",
    "governors/v43_unified_evidence", "governors/v44_error_learning",
    "governors/v45_validated_decisions", "governors/selftest_v35_v36",
    "governors/v46_honest_performance", "governors/v47_swing_edge",
    "governors/v48_short_swing_router", "governors/v49_short_swing_governor",
    "governors/v60_edge_router", "desk/v52_professional_core", "desk/v53_decision_dna",
    "desk/v54_replay_telegram", "desk/v55_signal_desk", "desk/v56_unified_desk",
    "desk/v56_2_governed_learning", "ui/v63_glass_v59_skin",
    "ui/v75_deep_coin_analysis", "analytics/v61_fast_scan",
    "analytics/v62_full_analytics", "analytics/v62_1_quality_patch",
    "analytics/v64_forecast_patterns", "analytics/v68_shadow_ledger",
    "analytics/v69_probability_cone", "analytics/v70_market_regime",
    "analytics/v71_pattern_validation", "platform/v72_pwa",
    "platform/v72_security_backup", "unified/v76_unified_pipeline",
    "hardening/v77_security", "hardening/v77_trace", "hardening/v77_diagnostics",
    "analytics/v78_realistic_forecast", "intel/v78_opportunity_funnel",
    "ui/v78_personalization", "hardening/v78_evaluation_dashboard",
    "hardening/v78_1_deep_activation", "hardening/v79_5_calibration_learning_queue",
    "hardening/v79_6_six_pillars", "hardening/v79_7_enterprise_contract",
    "hardening/v79_8_enterprise_infra", "hardening/v79_9_service_architecture",
    "hardening/v80_advanced_platform", "ui/v79_win11_glass_dashboard",
    "entry/main_entry"
]
CHAIN_NAMES = (
    "analyze_asset", "update_cache", "v55_desk_snapshot", "start_live_engine",
    "_v29_auto_loop", "fetch_derivatives", "get_depth_snapshot",
    "_dashboard_finalize_item", "_v51_build_authoritative", "run_titan",
)
LAYER_DIR = Path(__file__).resolve().parent / "layers"
_FLAGS = _fut.annotations.compiler_flag


def load(entry_file: str, as_main: bool = True, stop_before: str | None = None) -> dict:
    """Execute the configured layers into one shared namespace."""
    ns: dict = {
        "__name__": "__main__" if as_main else "titan_pro",
        "__file__": str(Path(entry_file).resolve()),
        "__package__": None,
        "__builtins__": __builtins__,
    }
    if not as_main:
        mod = types.ModuleType("titan_pro")
        mod.__dict__.update(ns)
        sys.modules["titan_pro"] = mod
        ns = mod.__dict__
    bindings: dict[str, list[str]] = {n: [] for n in CHAIN_NAMES}
    last_id: dict[str, int] = {}
    log: list[dict] = []
    ns["_TITAN_LAYER_BINDINGS"] = bindings
    ns["_TITAN_LAYER_LOG"] = log
    for name in LAYER_ORDER:
        if stop_before and name == stop_before:
            break
        # Chaquopy's AssetFinder exposes Python modules through its import loader;
        # its virtual paths are not real OS directories, so Path.is_file/read_text
        # incorrectly report packaged layers as missing on Android.
        module_name = "titan.layers." + name.replace("/", ".")
        try:
            import importlib.util
            spec = importlib.util.find_spec(module_name)
            if spec is None or spec.loader is None:
                raise FileNotFoundError(f"no import spec for {module_name}")
            get_source = getattr(spec.loader, "get_source", None)
            src = get_source(module_name) if callable(get_source) else None
            if not src:
                raise FileNotFoundError(f"source unavailable from loader for {module_name}")
            filename = spec.origin or str(LAYER_DIR / f"{name}.py")
            code = compile(src, filename, "exec", flags=_FLAGS, dont_inherit=True)
        except (OSError, ImportError, SyntaxError, FileNotFoundError) as exc:
            raise RuntimeError(f"Failed to load TITAN layer {name}: {exc}") from exc
        started = time.perf_counter()
        try:
            exec(code, ns)
        except Exception as exc:
            raise RuntimeError(f"Error while executing TITAN layer {name}: {exc}") from exc
        log.append({"layer": name, "lines": src.count("\n"), "ms": round((time.perf_counter()-started)*1000, 1)})
        for chain_name in CHAIN_NAMES:
            obj = ns.get(chain_name)
            if obj is not None and id(obj) != last_id.get(chain_name):
                last_id[chain_name] = id(obj)
                bindings[chain_name].append(name)
    ns["__version__"] = "80.0.0" if ns.get("V80_VERSION") else ns.get("__version__", "80.0.0")
    if ns.get("V80_VERSION"):
        ns.update({"__version__": "80.0.0", "V79_VERSION": "80.0.0",
                   "_TITAN_VERSION": "80.0.0"})
        ns["PIPELINE_VERSION"] = ns.get("PIPELINE_VERSION") or "80.0.0"
    else:
        ns.setdefault("__version__", "80.0.0")
        ns.setdefault("V79_VERSION", "80.0.0")
        ns["_TITAN_VERSION"] = ns.get("V79_UI_VERSION") or ns.get("V79_6_VERSION") or ns.get("__version__", "80.0.0")
    return ns
