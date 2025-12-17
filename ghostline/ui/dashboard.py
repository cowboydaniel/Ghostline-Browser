"""Privacy dashboard and quick toggles for network privacy controls.

This module wires Phase 3 fingerprinting defenses into the live browser UI by
owning uniformity presets, entropy budgeting, deterministic noise calibrators,
and container UX templates. The main window queries this dashboard to render
container badges and to surface summaries of the active protection posture for
each container.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from urllib.parse import urlsplit

from ghostline.networking.proxy import ProxyRegistry
from ghostline.privacy.entropy import DeviceRandomizer, EntropyBudget, NoiseCalibrator
from ghostline.privacy.uniformity import HIGH_ENTROPY_APIS, UniformityManager
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
    locale: str = "en-US"
    _container_templates: Dict[str, str] = field(default_factory=dict)
    _container_origins: Dict[str, str] = field(default_factory=dict)
    _last_device_class: Dict[str, Dict[str, str | int]] = field(default_factory=dict)

    def ensure_container(self, name: str, template: str = "research", locale: str | None = None) -> ContainerBadge:
        """Register container template, apply uniformity profile, and return badge."""

        badge = self.container_ux.badge_for(name)
        if badge is None:
            badge = self.container_ux.register_container(name, template)
        self._container_templates[name] = template

        profile_locale = locale or self.locale
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


__all__ = ["PrivacyDashboard"]
