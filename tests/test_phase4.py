from datetime import datetime, timedelta

import pytest

from ghostline.extensions.platform import (
    ExtensionManifest,
    ExtensionPackage,
    ExtensionPlatform,
    ResourceBudget,
)
from ghostline.permissions.manager import (
    NativeMessagingGuard,
    PermissionManager,
    PermissionPolicyEngine,
    PermissionPrompt,
)
from ghostline.ui.dashboard import PrivacyDashboard


def test_extension_store_gating_and_sandbox_alerts():
    platform = ExtensionPlatform()
    manifest = ExtensionManifest(
        name="translator",
        version="1.0.0",
        permissions=["tabs", "clipboard"],
        reference_hash="abc123",
    )
    package = ExtensionPackage(
        identifier="ext-translator",
        manifest=manifest,
        signature="sig",
        build_hash="abc123",
        provenance="ci",
    )

    platform.publish(package)
    platform.manager.allow_extension("alpha", package.identifier)
    platform.enable_for_container("alpha", package.identifier)

    gating = platform.manager.gated_permissions("alpha", package.identifier)
    assert gating["clipboard"] is False
    assert platform.manager.is_allowed("alpha", package.identifier)

    platform.sandbox.set_budget(package.identifier, ResourceBudget(cpu_ms=5, memory_mb=32, network_kb=16))
    platform.sandbox.record_usage(package.identifier, cpu_ms=10, memory_mb=1, network_kb=1)
    assert platform.sandbox.alerts

    platform.clone_container_policy("alpha", "beta")
    assert platform.manager.is_allowed("beta", package.identifier)
    assert package.identifier in platform.container_extensions("beta")


def test_permission_prompts_auto_revocation_and_one_time():
    policy = PermissionPolicyEngine(compliance_mode="strict")
    manager = PermissionManager(policy_engine=policy, idle_timeout=timedelta(seconds=1))
    origin = "https://example.com"

    prompt = PermissionPrompt(scope="camera", duration="once", data_access="video", purpose="call")
    grant = manager.request_permission(origin, "camera", prompt, one_time=True)
    assert grant.granted and grant.one_time and grant.active
    assert manager.use_permission(origin, "camera")

    # Force the permission to be idle long enough to trigger auto-revocation
    grant.mark_used(datetime.utcnow() - timedelta(seconds=5))
    manager.revoke_unused(now=datetime.utcnow())
    assert grant.active is False
    assert any(entry.get("reason") == "auto-revoked" for entry in manager.exposure_log)

    geo_prompt = PermissionPrompt(scope="geolocation", duration="session", data_access="coarse location", purpose="map")
    geo = manager.request_permission(origin, "geolocation", geo_prompt)
    assert geo.active
    manager.close_tab(origin)
    assert geo.active is False

    guard = NativeMessagingGuard({"com.example.host"})
    assert guard.validate("com.example.host", signed_host=True)
    assert guard.validate("com.unknown", signed_host=True) is False


def test_dashboard_surfaces_extension_and_permission_state():
    dashboard = PrivacyDashboard()
    dashboard.ensure_container("alpha", template="research")
    dashboard.record_navigation("alpha", "https://example.com")

    manifest = ExtensionManifest(
        name="privacy-auditor",
        version="2.0.0",
        permissions=["tabs", "nativeMessaging"],
        reference_hash="hash99",
    )
    package = ExtensionPackage(
        identifier="ext-auditor",
        manifest=manifest,
        signature="sig",
        build_hash="hash99",
        provenance="ci",
    )
    dashboard.register_extension(package, container="alpha")
    dashboard.extension_platform.sandbox.record_usage(package.identifier, cpu_ms=200, memory_mb=1, network_kb=1)

    prompt = PermissionPrompt(scope="geolocation", duration="session", data_access="coarse", purpose="map display")
    assert dashboard.request_permission("alpha", "geolocation", prompt)
    dashboard.log_permission_usage("alpha", "geolocation")

    summary = dashboard.status_for_container("alpha")
    assert package.identifier in summary["extensions"]
    assert "geolocation" in summary["permissions"]
    assert summary["policy_mode"] == dashboard.permission_policy.compliance_mode
    assert dashboard.sandbox_alerts()
    assert dashboard.permission_policy.export_audit()

    dashboard.clone_extension_policy("alpha", "beta")
    dashboard.ensure_container("beta", template="shopping")
    cloned_summary = dashboard.status_for_container("beta")
    assert package.identifier in cloned_summary["extensions"]
