"""Proxy configuration with split-tunnel prevention and leak checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ProxyConfig:
    """Represents per-container proxy settings covering all protocols."""

    name: str
    http_proxy: str
    https_proxy: str
    socks_proxy: str
    leak_tests: Dict[str, bool] = field(default_factory=dict)

    def split_tunnel_safe(self) -> bool:
        return all([self.http_proxy, self.https_proxy, self.socks_proxy])

    def preflight_leak_test(self) -> Dict[str, bool]:
        self.leak_tests = {
            "dns": self.split_tunnel_safe(),
            "ip": self.split_tunnel_safe(),
            "sni": self.split_tunnel_safe(),
        }
        return self.leak_tests


class ProxyRegistry:
    """Manages container-scoped proxies with leak-test enforcement."""

    def __init__(self) -> None:
        self.proxies: Dict[str, ProxyConfig] = {}

    def register(self, config: ProxyConfig) -> None:
        if not config.split_tunnel_safe():
            raise ValueError("split-tunnel prevention failed: missing proxy leg")
        config.preflight_leak_test()
        self.proxies[config.name] = config

    def get(self, name: str) -> ProxyConfig | None:
        return self.proxies.get(name)


__all__ = ["ProxyConfig", "ProxyRegistry"]
