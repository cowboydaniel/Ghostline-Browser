"""Privacy dashboard and quick toggles for network privacy controls."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ghostline.networking.proxy import ProxyRegistry


@dataclass
class PrivacyDashboard:
    """Summarizes connection state and exposes quick toggles."""

    connection_mode: str = "standard"
    proxy_registry: ProxyRegistry = field(default_factory=ProxyRegistry)
    errors: List[str] = field(default_factory=list)
    toggles: Dict[str, bool] = field(default_factory=lambda: {"ech": True, "tor": False, "https_only": True})

    def status_for_container(self, container: str) -> Dict[str, str | bool]:
        proxy = self.proxy_registry.get(container)
        return {
            "mode": self.connection_mode,
            "proxy": proxy.name if proxy else None,
            "ech": self.toggles.get("ech", False),
            "https_only": self.toggles.get("https_only", False),
            "tor": self.toggles.get("tor", False),
        }

    def log_error(self, message: str) -> None:
        self.errors.append(message)

    def toggle(self, key: str, enabled: bool) -> None:
        if key in self.toggles:
            self.toggles[key] = enabled
        else:
            self.errors.append(f"unknown-toggle:{key}")


__all__ = ["PrivacyDashboard"]
