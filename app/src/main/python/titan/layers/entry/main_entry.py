# [TITAN V78 layer] entry/main_entry — __main__ block, always runs last.
"""Process entry: self-tests or start the HTTP server. V78 includes evaluation, forecast, funnel, UI."""

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"--self-test", "--test", "self-test"}:
        self_tests = [
            (_titan_self_test, "legacy"),
            (_v45_self_test, "v45"),
            (_v46_self_test, "v46"),
            (_v47_self_test, "v47"),
            (_v48_self_test, "v48"),
            (_v49_self_test, "v49"),
            (_v52_self_test, "v52"),
            (_v53_self_test, "v53"),
            (_v54_self_test, "v54"),
            (_v55_self_test, "v55"),
            (_v56_self_test, "v56"),
            (_titan_governed_self_test, "governed_learning"),
            (_v62_patch_self_test, "v62.1_data_quality"),
            (_v72_self_test, "v72_security_backup_sqlite"),
            (_v76_self_test, "v76_unified_forecast"),
            (_v77_self_test, "v77_security_trace_layers"),
            (_v78_self_test, "v78_evaluation"),
            (_v78_forecast_self_test, "v78_realistic_forecast"),
            (_v78_funnel_self_test, "v78_opportunity_funnel"),
            (_v78_ui_self_test, "v78_ui_personalization"),
            (_v78_1_self_test, "v78_1_deep_activation"),
            (_v79_7_self_test, "v79_7_enterprise_contract"),
            (_v79_8_self_test, "v79_8_enterprise_infra"),
            (_v79_9_self_test, "v79_9_service_architecture"),
            (_v80_self_test, "v80_advanced_platform"),
        ]
        rc = 0
        for fn, name in self_tests:
            try:
                rc = max(rc, int(fn()))
            except Exception as exc:
                print(f"{name} self-test error: {exc}")
                rc = 1
        raise SystemExit(rc)

    open_browser = str(os.environ.get("TITAN_OPEN_BROWSER", "0")).lower() in {
        "1",
        "true",
        "yes",
    }
    run_titan(open_browser=open_browser)
