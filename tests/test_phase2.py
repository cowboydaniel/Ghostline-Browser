import pytest

from ghostline.networking.dns import EncryptedDNSResolver
from ghostline.networking.hygiene import CertPinningPolicy, ProxyLeakSuite, WebRTCPolicy
from ghostline.networking.proxy import ProxyConfig, ProxyRegistry
from ghostline.networking.tor import TorController
from ghostline.ui.dashboard import PrivacyDashboard


def test_encrypted_dns_fallback_and_ech_toggle():
    resolver = EncryptedDNSResolver()
    result = resolver.resolve("example.com", simulate_failure="doh")
    assert result["method"] == "dot"
    resolver.disable_ech()
    second = resolver.resolve("example.com", prefer="dot")
    assert not second["ech"]
    assert "fallback:example.com:doh" in resolver.leak_log


def test_proxy_registry_split_tunnel_prevention_and_suite():
    registry = ProxyRegistry()
    cfg = ProxyConfig(name="container-a", http_proxy="http://h", https_proxy="http://s", socks_proxy="socks5://p")
    registry.register(cfg)

    suite = ProxyLeakSuite()
    results = suite.run(cfg.leak_tests)
    assert all(results.values())

    with pytest.raises(ValueError):
        registry.register(ProxyConfig(name="bad", http_proxy="", https_proxy="http://s", socks_proxy="socks5://p"))


def test_tor_controller_isolates_and_rotates_on_fingerprint_errors():
    tor = TorController()
    tor.enable()
    circuit = tor.isolate_stream("one")
    rotated = tor.mark_fingerprint_error("one")
    assert circuit.guard_node != rotated.guard_node
    assert not rotated.healthy
    assert tor.bootstrap_status() in tor.bootstrap_steps


def test_webrtc_policy_and_cert_pinning():
    policy = WebRTCPolicy()
    assert policy.candidate_allowed("stun:stun.example.org")
    assert not policy.candidate_allowed("stun:untrusted.example")

    pinning = CertPinningPolicy()
    pinning.pin("ghostline.test", "abc123")
    assert pinning.verify("ghostline.test", "abc123")
    pinning.record_ocsp("ghostline.test")
    pinning.crlite_coverage.add("ghostline.test")
    assert pinning.has_crlite("ghostline.test")


def test_privacy_dashboard_toggles_and_status():
    registry = ProxyRegistry()
    cfg = ProxyConfig(name="container-ui", http_proxy="http://h", https_proxy="http://s", socks_proxy="socks5://p")
    registry.register(cfg)

    dashboard = PrivacyDashboard(proxy_registry=registry, connection_mode="tor")
    dashboard.toggle("tor", True)
    status = dashboard.status_for_container("container-ui")
    assert status["proxy"] == "container-ui"
    assert status["tor"] is True
