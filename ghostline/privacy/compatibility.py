"""Compatibility helpers for known site breakages and remediation tips."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urlparse


@dataclass(frozen=True)
class CompatibilityAdvisory:
    """Describes a known site issue and how to address it."""

    host: str
    error_code: str
    symptom: str
    remediation: str

    def matches(self, host: str) -> bool:
        return host == self.host or host.endswith(f".{self.host}")


class StreamingCompatibilityAdvisor:
    """Identifies DRM-related streaming failures and suggests fixes."""

    def __init__(self, advisories: Optional[Iterable[CompatibilityAdvisory]] = None) -> None:
        self._advisories = tuple(advisories) if advisories else self._default_advisories()

    def advisory_for(self, host_or_url: str) -> Optional[CompatibilityAdvisory]:
        host = self._normalize_host(host_or_url)
        if not host:
            return None

        for advisory in self._advisories:
            if advisory.matches(host):
                return advisory
        return None

    @staticmethod
    def _normalize_host(value: str) -> Optional[str]:
        if not value:
            return None

        if "://" in value:
            parsed = urlparse(value)
            host = parsed.hostname
        else:
            host = value

        if not host:
            return None

        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    @staticmethod
    def _default_advisories() -> tuple[CompatibilityAdvisory, ...]:
        return (
            CompatibilityAdvisory(
                host="netflix.com",
                error_code="M7701-1003",
                symptom="Encrypted Media Extensions / Widevine CDM unavailable for playback",
                remediation=(
                    "Enable Widevine/DRM components for this profile or use a system profile that"
                    " permits EME playback; disabling privacy hardening for media may be required."
                ),
            ),
        )

