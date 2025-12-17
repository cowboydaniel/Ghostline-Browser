"""Performance profiling and resource overlay helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ProfileSample:
    cold_start_ms: int
    page_load_ms: int
    input_latency_ms: int


@dataclass
class UsageOverlay:
    power_mw: int
    cpu_percent: float
    bandwidth_kbps: int
    recommendation: str


class PerformanceMonitor:
    """Tracks performance profiles and resource usage overlays per container."""

    def __init__(self) -> None:
        self.profiles: Dict[str, ProfileSample] = {}
        self.overlays: Dict[str, List[UsageOverlay]] = {}

    def profile_page(self, site: str, cold_start_ms: int, page_load_ms: int, input_latency_ms: int) -> ProfileSample:
        sample = ProfileSample(cold_start_ms=cold_start_ms, page_load_ms=page_load_ms, input_latency_ms=input_latency_ms)
        self.profiles[site] = sample
        return sample

    def record_usage(self, container: str, power_mw: int, cpu_percent: float, bandwidth_kbps: int) -> UsageOverlay:
        recommendation = self._recommend(power_mw, cpu_percent, bandwidth_kbps)
        overlay = UsageOverlay(
            power_mw=power_mw,
            cpu_percent=cpu_percent,
            bandwidth_kbps=bandwidth_kbps,
            recommendation=recommendation,
        )
        self.overlays.setdefault(container, []).append(overlay)
        return overlay

    def overlays_for(self, container: str) -> List[UsageOverlay]:
        return list(self.overlays.get(container, []))

    def _recommend(self, power_mw: int, cpu_percent: float, bandwidth_kbps: int) -> str:
        if power_mw > 800 or cpu_percent > 80:
            return "Throttle background tabs and disable animations"
        if bandwidth_kbps > 5_000:
            return "Enable data-saver and pause media-heavy pages"
        return "All clear"


__all__ = ["PerformanceMonitor", "ProfileSample", "UsageOverlay"]
