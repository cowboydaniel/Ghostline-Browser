"""Connection hygiene primitives for leak testing and certificate pinning."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class WebRTCPolicy:
    """Enforces defaults that reduce IP leak exposure."""

    mdns_enabled: bool = True
    ice_policy: str = "relay-only"
    stun_allowlist: Set[str] = field(default_factory=lambda: {"stun:stun.example.org"})
    turn_allowlist: Set[str] = field(default_factory=lambda: {"turn:turn.example.org"})

    def candidate_allowed(self, url: str) -> bool:
        return url in self.stun_allowlist or url in self.turn_allowlist


@dataclass
class ProxyLeakSuite:
    """Aggregates DNS/IP/SNI/timing leak checks used before releases."""

    results: Dict[str, bool] = field(default_factory=dict)

    def run(self, proxy_summary: Dict[str, bool]) -> Dict[str, bool]:
        self.results = {
            "dns": proxy_summary.get("dns", False),
            "ip": proxy_summary.get("ip", False),
            "sni": proxy_summary.get("sni", False),
            "timing": all(proxy_summary.values()),
        }
        return self.results


@dataclass
class CertPinningPolicy:
    """Minimal certificate pinning and revocation verification helper."""

    pins: Dict[str, str] = field(default_factory=dict)
    ocsp_stapled: List[str] = field(default_factory=list)
    crlite_coverage: Set[str] = field(default_factory=set)

    def pin(self, host: str, fingerprint: str) -> None:
        self.pins[host] = fingerprint

    def verify(self, host: str, fingerprint: str) -> bool:
        return self.pins.get(host) == fingerprint

    def record_ocsp(self, host: str) -> None:
        if host not in self.ocsp_stapled:
            self.ocsp_stapled.append(host)

    def has_crlite(self, host: str) -> bool:
        return host in self.crlite_coverage


__all__ = ["WebRTCPolicy", "ProxyLeakSuite", "CertPinningPolicy"]
