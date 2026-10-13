"""Layer loader for TITAN PRO V80.

Why not plain imports?  The V8..V80 layers deliberately *wrap* module-level names
(analyze_asset, update_cache, v55_desk_snapshot, ...) and read each other through
globals().  Separate module namespaces would silently break that contract, so every
layer file is compiled with its real filename (clean tracebacks) and executed, in
order, into ONE shared namespace.

The loader also records WHICH layer (re)bound each wrapped name, so the V53 / V55 /
V56 / V62 / V78 chains are explicit and inspectable (GET /api/v77/layers + /api/v78/*).
"""
from __future__ import annotations

import __future__ as _fut
import sys
import time
import types
from pathlib import Path

LAYER_ORDER = [
    "core/bootstrap_storage",
    "core/logging_safety_keys",
    "core/defaults_helpers",
    "core/confidence_v8",
    "data/storage_sqlite",
    "data/market_http",
    "decision/technicals_core",
    "decision/neural_synapse_v9",
    "decision/signal_grade_v10",
    "decision/decision_core_v3",
    "decision/ai_layer",
    "analysis/asset_analysis",
    "analysis/professional_edge_suite",
    "analysis/adaptive_intelligence",
    "engine/paper_forecast_metrics",
    "engine/backtest_walkforward",
    "engine/live_engine",
    "engine/cache_command_center",
    "engine/advanced_metrics",
    "engine/performance_snapshot",
    "engine/enterprise_audit_validation",
    "web/flask_app",
    "intel/v10_5_cognitive_nexus",
    "intel/v21_trust_max",
    "intel/v22_opportunity",
    "intel/v29_evidence_fusion",
    "intel/v30_deep_consensus",
    "intel/v31_canonical_decision",
    "intel/v32_performance_learning",
    "web/routes_startup",
    "governors/v29_3_central_governor",
    "governors/v29_5_edge_lab",
    "governors/v31_advanced_edge_suite",
    "governors/v34_adaptive_trust",
    "governors/v35_live_price_levels",
    "governors/v36_quantum_resonance",
    "governors/v40_five_hard_fixes",
    "governors/v42_integrity_seal",
    "governors/v43_unified_evidence",
    "governors/v44_error_learning",
    "governors/v45_validated_decisions",
    "governors/selftest_v35_v36",
    "governors/v46_honest_performance",
    "governors/v47_swing_edge",
    "governors/v48_short_swing_router",
    "governors/v49_short_swing_governor",
    "governors/v60_edge_router",
    "desk/v52_professional_core",
    "desk/v53_decision_dna",
    "desk/v54_replay_telegram",
    "desk/v55_signal_desk",
    "desk/v56_unified_desk",
    "desk/v56_2_governed_learning",
    "ui/v63_glass_v59_skin",
    "ui/v75_deep_coin_analysis",
    "analytics/v61_fast_scan",
    "analytics/v62_full_analytics",
    "analytics/v62_1_quality_patch",
    "analytics/v64_forecast_patterns",
    "analytics/v68_shadow_ledger",
    "analytics/v69_probability_cone",
    "analytics/v70_market_regime",
    "analytics/v71_pattern_validation",
    "platform/v72_pwa",
    "platform/v72_security_backup",
    "unified/v76_unified_pipeline",
    "hardening/v77_security",
    "hardening/v77_trace",
    "hardening/v77_diagnostics",
    # ---- V78 advanced modules (evaluation, realistic forecast, funnel, UI) ----
    "analytics/v78_realistic_forecast",
    "intel/v78_opportunity_funnel",
    "ui/v78_personalization",
    "hardening/v78_evaluation_dashboard",
    # ---- V78.1 deep activation: consensus strengthen + full UI wire + force-activate ----
    "hardening/v78_1_deep_activation",
    "hardening/v79_5_calibration_learning_queue",
    "hardening/v79_6_six_pillars",
    "hardening/v79_7_enterprise_contract",
    "hardening/v79_8_enterprise_infra",
    "hardening/v79_9_service_architecture",
    "hardening/v80_advanced_platform",
    "ui/v79_win11_glass_dashboard",
    "entry/main_entry",
]

LAYER_DIR = Path(__file__).resolve().parent / "layers"

# Names that successive layers intentionally rebind; tracked for transparency.
CHAIN_NAMES = (
    "analyze_asset",
    "update_cache",
    "v55_desk_snapshot",
    "v56_unified_desk",
    "v62_full_analytics",
    "v78_realistic_forecast",
    "app",
    "run_titan",
)

_FLAGS = _fut.annotations.compiler_flag


def load(entry_file: str, as_main: bool = True, stop_before: str | None = None) -> dict:
    """Execute all layers into one namespace and return it.

    stop_before: layer name at which to stop (used by tests to avoid running __main__).
    """
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
        path = LAYER_DIR / f"{name}.py"
        if not path.is_file():
            raise FileNotFoundError(f"TITAN layer missing: {path}")
        try:
            src = path.read_text(encoding="utf-8")
            code = compile(src, str(path), "exec", flags=_FLAGS, dont_inherit=True)
        except (OSError, SyntaxError) as exc:
            raise RuntimeError(f"Failed to load TITAN layer {name}: {exc}") from exc
        t0 = time.perf_counter()
        try:
            exec(code, ns)
        except Exception as exc:
            raise RuntimeError(f"Error while executing TITAN layer {name}: {exc}") from exc
        log.append({"layer": name, "lines": src.count("\n"), "ms": round((time.perf_counter() - t0) * 1000, 1)})
        for cn in CHAIN_NAMES:
            obj = ns.get(cn)
            if obj is not None and id(obj) != last_id.get(cn):
                last_id[cn] = id(obj)
                bindings[cn].append(name)
    # Professional: single source of truth for package version after all layers
    ns["__version__"] = ns.get("V80_VERSION") and "80.0.0" or ns.get("__version__", "80.0.0")
    if ns.get("V80_VERSION"):
        ns["__version__"] = "80.0.0"
        ns["V79_VERSION"] = "80.0.0"
        ns["_TITAN_VERSION"] = "80.0.0"
        ns["PIPELINE_VERSION"] = ns.get("PIPELINE_VERSION") or "80.0.0"
    else:
        ns.setdefault("__version__", "80.0.0")
        ns.setdefault("V79_VERSION", "80.0.0")
        ns["_TITAN_VERSION"] = ns.get("V79_UI_VERSION") or ns.get("V79_6_VERSION") or ns.get("__version__", "80.0.0")
    return ns
