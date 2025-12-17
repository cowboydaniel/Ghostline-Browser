from ghostline.community.publishing import ReleaseCommunicator
from ghostline.community.publishing import ReleaseCommunicator
from ghostline.devops.reliability import PrivacyCIOrchestrator, ReproducibilityDashboard, RolloutController
from ghostline.operations.incident import CrashTelemetryPipeline, OnCallRotation, RedTeamProgram
from ghostline.performance.monitor import PerformanceMonitor
from ghostline.ui.dashboard import PrivacyDashboard


def test_privacy_ci_reproducibility_and_rollouts():
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("alpha", template="research")
    dashboard.ensure_container("beta", template="research")

    proxy_summary = {"dns": True, "ip": True, "sni": True, "timing": True}
    ci_results = dashboard.run_privacy_ci(proxy_summary)
    assert ci_results["uniformity_consistent"]
    assert ci_results["leaks"]["dns"]

    repro = ReproducibilityDashboard()
    repro.record_artifact("nightly", "browser", "abc")
    repro.record_artifact("beta", "browser", "abc")
    repro.record_artifact("stable", "browser", "xyz")
    assert repro.variance_alerts

    rollout = RolloutController()
    rollout.register_feature("privacy-ci", cohort="canary")
    rollout.assign_cohort("user123", "canary")
    rollout.enable_feature("privacy-ci")
    assert rollout.evaluate("user123", "privacy-ci")
    rollout.kill_switch("privacy-ci")
    assert rollout.evaluate("user123", "privacy-ci") is False


def test_incident_response_performance_and_community_overlays():
    telemetry = CrashTelemetryPipeline(sample_rate=1.0, budget=2)
    sanitized = telemetry.sanitize({"signature": "sig1", "stack": "trace", "email": "p@e"})
    assert "email" not in sanitized
    assert telemetry.submit(sanitized)
    assert telemetry.submit({"signature": "sig2", "stack": "trace", "ip": "1.1.1.1"})

    program = RedTeamProgram()
    exercise = program.schedule_exercise("fingerprinting bypass")
    program.record_result(exercise, "open", ["canvas-noise-tuned"])
    assert program.open_findings

    oncall = OnCallRotation(["alice", "bob"])
    oncall.add_runbook("privacy regression", "check uniformity masks")
    oncall.add_playbook("network leak", ["rotate guards", "run leak suite"])
    assert oncall.current_oncall() == "alice"
    assert oncall.runbooks["privacy regression"].startswith("check")

    performance = PerformanceMonitor()
    performance.profile_page("https://example.com", cold_start_ms=120, page_load_ms=450, input_latency_ms=35)
    overlay = performance.record_usage("alpha", power_mw=900, cpu_percent=85, bandwidth_kbps=100)
    assert "Throttle" in overlay.recommendation

    dashboard = PrivacyDashboard()
    dashboard.ensure_container("delta", template="shopping")
    dashboard.record_usage_metrics("delta", power_mw=200, cpu_percent=15, bandwidth_kbps=1000)
    overlays = dashboard.status_for_container("delta")["performance_overlays"]
    assert overlays
    dashboard.record_usability_study("permissions", "prompt clarity improved")
    assert dashboard.usability_findings

    comms = ReleaseCommunicator()
    comms.record_test_harness("proxy leak harness")
    comms.update_matrix("extensions", "nativeMessaging", "deprecated")
    published = comms.publish_release(
        "1.0", ["tor"], ["architecture.md"], ["staged rollouts", "privacy ci"]
    )
    assert published.version == "1.0"
    assert comms.compatibility_matrix["extensions"]["nativeMessaging"] == "deprecated"
