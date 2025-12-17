import pytest

from ghostline.privacy.audit import ExternalTestbedIntegration, FingerprintingAuditSuite, PrivacyScorecard
from ghostline.privacy.entropy import DeviceRandomizer, EntropyBudget, NoiseCalibrator
from ghostline.privacy.uniformity import HIGH_ENTROPY_APIS, UniformityManager
from ghostline.ui.containers import ContainerUX


def test_uniformity_presets_gate_high_entropy_and_fonts():
    manager = UniformityManager()
    strict_profile = manager.apply_preset("alpha", "strict", locale="en-US")
    manager.apply_preset("beta", "balanced", locale="fr-FR")

    assert strict_profile.capability_mask == {api: False for api in HIGH_ENTROPY_APIS}
    assert manager.gate_api("alpha", "webgpu") is False
    assert manager.gate_api("beta", "webgpu") is False

    default_fonts = manager.fonts_for("alpha", "en-US")
    manager.set_site_override("alpha", "example.com", ["Inter", "Ghostline Sans"])
    assert manager.fonts_for("alpha", "en-US", site="example.com") != default_fonts
    assert manager.fonts_for("beta", "fr-FR")[0] == "Inter"


def test_entropy_budget_and_device_randomization():
    budget = EntropyBudget(limit_bits=8)
    assert budget.consume("canvas", 3)
    assert budget.consume("webgl", 4)
    assert budget.consume("audio", 2) is False
    assert any(evt.startswith("budget-exceeded") for evt in budget.devtools_events)
    assert budget.telemetry_events

    randomizer = DeviceRandomizer(seed="phase3", stability_window=2)
    first = randomizer.randomize(window_id=1)
    second = randomizer.randomize(window_id=1)
    assert first == second
    rotated = randomizer.randomize(window_id=3)
    assert rotated != first

    noise = NoiseCalibrator(amplitude=0.3)
    canvas_noise = noise.canvas_noise("https://example.com")
    assert all(-0.3 <= v <= 0.3 for v in canvas_noise.values())
    assert -0.15 <= noise.audio_noise("https://example.com") <= 0.15


def test_fingerprinting_audits_and_scorecards():
    manager = UniformityManager()
    manager.apply_preset("alpha", "balanced")
    manager.apply_preset("beta", "balanced")
    audit = FingerprintingAuditSuite()
    result = audit.compare_uniformity(manager, ["alpha", "beta"])
    assert result.consistent
    assert result.uniformity_delta["alpha"] == 0

    external = ExternalTestbedIntegration()
    external.record_snapshot({"entropy": 10, "failures": 2})
    external.record_snapshot({"entropy": 8, "failures": 1})
    diff = external.latest_diff()
    assert diff["entropy"] == -2
    assert diff["failures"] == -1

    scorecard = PrivacyScorecard(
        release="0.3", entropy_deltas={"uniformity": -2}, mitigations=["Canvas noise", "API gating"], audit_notes=result.notes
    )
    rendered = scorecard.render()
    assert "Ghostline 0.3 Privacy Scorecard" in rendered
    assert "Canvas noise" in rendered


def test_container_ux_templates_and_badges():
    ux = ContainerUX()
    badge = ux.register_container("research-tab", "research")
    assert badge.policy.tor_required
    assert badge.color.startswith("#")
    shopping = ux.register_container("shopping-tab", "shopping")
    assert shopping.policy.uniformity_preset == "balanced"
    assert ux.badge_for("research-tab").isolation_badge.startswith("isolated")

    with pytest.raises(ValueError):
        ux.register_container("unknown", "invalid")
