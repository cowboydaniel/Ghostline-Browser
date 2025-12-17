"""Encrypted DNS resolver with ECH and leak detection fallbacks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class EncryptedDNSResolver:
    """Models DoH/DoT resolution with ECH toggles and leak tracking."""

    doh_endpoint: str = "https://doh.example/dns-query"
    dot_endpoint: str = "tls://dot.example:853"
    ech_enabled: bool = True
    leak_log: List[str] = field(default_factory=list)

    def resolve(self, hostname: str, prefer: str = "doh", simulate_failure: str | None = None) -> Dict[str, str | bool]:
        """Resolve a hostname preferring encrypted transports.

        ``simulate_failure`` allows tests to exercise fallback paths without performing
        network I/O. When the preferred method fails, the resolver transparently
        downgrades while recording a leak candidate.
        """

        method = prefer
        if simulate_failure == prefer:
            self.leak_log.append(f"fallback:{hostname}:{prefer}")
            method = "dot" if prefer == "doh" else "doh"

        leak_detected = method not in {"doh", "dot"}
        if leak_detected:
            self.leak_log.append(f"leak:{hostname}:{method}")

        ech_state = self.ech_enabled and method == "doh"
        return {
            "hostname": hostname,
            "method": method,
            "ech": ech_state,
            "leak_detected": leak_detected,
        }

    def disable_ech(self) -> None:
        self.ech_enabled = False
        self.leak_log.append("ech-disabled")


__all__ = ["EncryptedDNSResolver"]
