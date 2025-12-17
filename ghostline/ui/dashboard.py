"""Privacy dashboard and quick toggles for network privacy controls.

This module wires Phase 3 fingerprinting defenses and the Phase 4 extension
and permission controls into the live browser UI by owning uniformity presets,
entropy budgeting, deterministic noise calibrators, extension policy cloning,
and container UX templates. The main window queries this dashboard to render
container badges and to surface summaries of the active protection posture for
each container.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from urllib.parse import urlsplit

from ghostline.extensions.platform import ExtensionPackage, ExtensionPlatform
from ghostline.devops.reliability import PrivacyCIOrchestrator, RolloutController
from ghostline.operations.incident import CrashTelemetryPipeline, OnCallRotation, RedTeamProgram
from ghostline.performance.monitor import PerformanceMonitor
from ghostline.networking.proxy import ProxyRegistry
from ghostline.permissions.manager import (
    NativeMessagingGuard,
    PermissionManager,
    PermissionPolicyEngine,
    PermissionPrompt,
)
from ghostline.privacy.entropy import DeviceRandomizer, EntropyBudget, NoiseCalibrator
from ghostline.privacy.uniformity import HIGH_ENTROPY_APIS, UniformityManager
from ghostline.community.publishing import ReleaseCommunicator
from ghostline.ui.containers import ContainerBadge, ContainerUX


def _origin_from_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "about:blank"


@dataclass
class PrivacyDashboard:
    """Summarizes connection state and exposes quick toggles."""

    connection_mode: str = "standard"
    proxy_registry: ProxyRegistry = field(default_factory=ProxyRegistry)
    errors: List[str] = field(default_factory=list)
    toggles: Dict[str, bool] = field(default_factory=lambda: {"ech": True, "tor": False, "https_only": True})
    uniformity_manager: UniformityManager = field(default_factory=UniformityManager)
    entropy_budget: EntropyBudget = field(default_factory=lambda: EntropyBudget(limit_bits=12))
    device_randomizer: DeviceRandomizer = field(default_factory=DeviceRandomizer)
    noise_calibrator: NoiseCalibrator = field(default_factory=NoiseCalibrator)
    container_ux: ContainerUX = field(default_factory=ContainerUX)
    permission_policy: PermissionPolicyEngine = field(default_factory=PermissionPolicyEngine)
    permission_manager: PermissionManager = field(init=False)
    native_messaging_guard: NativeMessagingGuard = field(default_factory=lambda: NativeMessagingGuard(set()))
    extension_platform: ExtensionPlatform = field(default_factory=ExtensionPlatform)
    ci_orchestrator: PrivacyCIOrchestrator = field(default_factory=PrivacyCIOrchestrator)
    rollout_controller: RolloutController = field(default_factory=RolloutController)
    telemetry_pipeline: CrashTelemetryPipeline = field(default_factory=CrashTelemetryPipeline)
    red_team_program: RedTeamProgram = field(default_factory=RedTeamProgram)
    oncall: OnCallRotation = field(default_factory=OnCallRotation)
    performance_monitor: PerformanceMonitor = field(default_factory=PerformanceMonitor)
    release_communicator: ReleaseCommunicator = field(default_factory=ReleaseCommunicator)
    usability_findings: List[str] = field(default_factory=list)
    locale: str = "en-US"
    _container_templates: Dict[str, str] = field(default_factory=dict)
    _container_origins: Dict[str, str] = field(default_factory=dict)
    _container_locales: Dict[str, str] = field(default_factory=dict)
    _last_device_class: Dict[str, Dict[str, str | int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.permission_manager = PermissionManager(policy_engine=self.permission_policy)

    def ensure_container(self, name: str, template: str = "research", locale: str | None = None) -> ContainerBadge:
        """Register container template, apply uniformity profile, and return badge."""

        badge = self.container_ux.badge_for(name)
        if badge is None:
            badge = self.container_ux.register_container(name, template)
        self._container_templates[name] = template

        if badge.policy.tor_required:
            self.ci_orchestrator.tor_controller.enable()
            self.ci_orchestrator.tor_controller.isolate_stream(name)

        profile_locale = locale or self.locale
        self._container_locales[name] = profile_locale
        self.uniformity_manager.apply_preset(name, badge.policy.uniformity_preset, locale=profile_locale)
        return badge

    def status_for_container(self, container: str) -> Dict[str, str | bool | Dict[str, str | int]]:
        proxy = self.proxy_registry.get(container)
        profile = self.uniformity_manager.profile_for(container)
        self._container_origins.setdefault(container, "about:blank")
        last_device = self._last_device_class.get(container, {})
        return {
            "mode": self.connection_mode,
            "proxy": proxy.name if proxy else None,
            "ech": self.toggles.get("ech", False),
            "https_only": self.toggles.get("https_only", False),
            "tor": self.toggles.get("tor", False),
            "uniformity": profile.name,
            "entropy_bits": self.entropy_budget.total_bits(),
            "container_origin": self._container_origins[container],
            "device_class": last_device or {},
            "extensions": self.extension_platform.container_extensions(container),
            "permissions": self.permission_manager.active_permissions(self._container_origins[container]),
            "policy_mode": self.permission_policy.compliance_mode,
            "performance_overlays": [overlay.recommendation for overlay in self.performance_monitor.overlays_for(container)],
        }

    def log_error(self, message: str) -> None:
        self.errors.append(message)

    def toggle(self, key: str, enabled: bool) -> None:
        if key in self.toggles:
            self.toggles[key] = enabled
        else:
            self.errors.append(f"unknown-toggle:{key}")

    def set_uniformity(self, container: str, preset: str, locale: str | None = None) -> None:
        profile_locale = locale or self.locale
        self.uniformity_manager.apply_preset(container, preset, locale=profile_locale)

    def record_navigation(self, container: str, url: str) -> None:
        """Reset entropy budget and randomize device class for a navigation."""

        origin = _origin_from_url(url)
        self._container_origins[container] = origin
        self.entropy_budget.reset()
        bucket_seed = abs(hash(origin)) % 10_000
        device = self.device_randomizer.randomize(window_id=bucket_seed)
        self._last_device_class[container] = device

    def request_permission(self, container: str, permission: str, prompt: PermissionPrompt) -> bool:
        origin = self._container_origins.get(container, "about:blank")
        grant = self.permission_manager.request_permission(origin, permission, prompt)
        return grant.granted and grant.active

    def log_permission_usage(self, container: str, permission: str) -> bool:
        origin = self._container_origins.get(container, "about:blank")
        return self.permission_manager.use_permission(origin, permission)

    def auto_revoke_permissions(self) -> None:
        self.permission_manager.revoke_unused()

    def register_extension(self, package: ExtensionPackage, container: str) -> None:
        self.extension_platform.publish(package)
        self.extension_platform.manager.allow_extension(container, package.identifier)
        self.extension_platform.enable_for_container(container, package.identifier)

    def clone_extension_policy(self, source: str, target: str) -> None:
        self.extension_platform.clone_container_policy(source, target)

    def sandbox_alerts(self) -> List[str]:
        return list(self.extension_platform.sandbox.alerts)

    def gating_snapshot(self, container: str, apis: List[str] | None = None) -> Dict[str, bool]:
        apis = apis or list(HIGH_ENTROPY_APIS)
        snapshot: Dict[str, bool] = {}
        for api in apis:
            snapshot[api] = self.uniformity_manager.gate_api(container, api)
        return snapshot

    def calibrated_noise_for(self, container: str) -> Dict[str, Dict[str, float] | float]:
        origin = self._container_origins.get(container, "about:blank")
        return {
            "canvas": self.noise_calibrator.canvas_noise(origin),
            "audio": self.noise_calibrator.audio_noise(origin),
        }

    def screen_dimensions_for(self, container: str) -> Dict[str, int]:
        """Get randomized screen dimensions for a container.

        Args:
            container: Container name

        Returns:
            Dictionary with screen dimension properties
        """
        origin = self._container_origins.get(container, "about:blank")
        bucket_seed = abs(hash(origin)) % 10_000
        return self.device_randomizer.screen_dimensions(window_id=bucket_seed)

    def record_usage_metrics(self, container: str, power_mw: int, cpu_percent: float, bandwidth_kbps: int) -> None:
        self.performance_monitor.record_usage(container, power_mw=power_mw, cpu_percent=cpu_percent, bandwidth_kbps=bandwidth_kbps)

    def run_privacy_ci(self, proxy_summary: Dict[str, bool]) -> Dict[str, object]:
        containers = list(self._container_templates.keys())
        return self.ci_orchestrator.run(self.uniformity_manager, containers, proxy_summary)

    def publish_release_comms(self, version: str, mitigations: List[str]) -> None:
        threat_models = [f"container:{name}" for name in self._container_templates]
        architecture_docs = ["threat-models.md", "privacy-ci.md"]
        self.release_communicator.publish_release(version, threat_models, architecture_docs, mitigations)

    def submit_crash(self, report: Dict[str, str]) -> bool:
        sanitized = self.telemetry_pipeline.sanitize(report)
        return self.telemetry_pipeline.submit(sanitized)

    def record_usability_study(self, topic: str, finding: str) -> None:
        self.usability_findings.append(f"{topic}:{finding}")


__all__ = ["PrivacyDashboard"]
