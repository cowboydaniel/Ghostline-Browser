"""Fingerprinting audit suites and scorecard generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ghostline.privacy.uniformity import UniformityManager, UniformityProfile


@dataclass
class AuditResult:
    uniformity_delta: Dict[str, int]
    consistent: bool
    notes: List[str] = field(default_factory=list)


class FingerprintingAuditSuite:
    """Compares uniformity across containers and profiles."""

    def compare_uniformity(self, manager: UniformityManager, containers: List[str]) -> AuditResult:
        if not containers:
            raise ValueError("no-containers")
        baseline = manager.profile_for(containers[0])
        delta: Dict[str, int] = {}
        consistent = True
        notes: List[str] = []

        for container in containers:
            profile = manager.profile_for(container)
            diff = self._diff_profiles(baseline, profile)
            delta[container] = diff
            if diff != 0:
                consistent = False
                notes.append(f"delta:{container}:{diff}")
        return AuditResult(uniformity_delta=delta, consistent=consistent, notes=notes)

    def _diff_profiles(self, baseline: UniformityProfile, other: UniformityProfile) -> int:
        diff = 0
        for api, allowed in baseline.capability_mask.items():
            if other.capability_mask.get(api, True) != allowed:
                diff += 1
        base_fonts = baseline.font_pack.locales.get("default", [])
        other_fonts = other.font_pack.locales.get("default", [])
        if base_fonts != other_fonts:
            diff += 1
        return diff


@dataclass
class ExternalTestbedIntegration:
    """Stores external fingerprint testbed snapshots for CI comparisons."""

    snapshots: List[Dict[str, int]] = field(default_factory=list)

    def record_snapshot(self, results: Dict[str, int]) -> None:
        self.snapshots.append(results)

    def latest_diff(self) -> Dict[str, int]:
        if len(self.snapshots) < 2:
            return {}
        previous, current = self.snapshots[-2], self.snapshots[-1]
        diff: Dict[str, int] = {}
        for key, value in current.items():
            prev_value = previous.get(key, 0)
            diff[key] = value - prev_value
        return diff


@dataclass
class PrivacyScorecard:
    """Publishes privacy scorecards for releases."""

    release: str
    entropy_deltas: Dict[str, int]
    mitigations: List[str]
    audit_notes: List[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"Ghostline {self.release} Privacy Scorecard"]
        lines.append("Entropy deltas:")
        for key, delta in self.entropy_deltas.items():
            lines.append(f"- {key}: {delta} bits")
        lines.append("Mitigations:")
        for mitigation in self.mitigations:
            lines.append(f"- {mitigation}")
        if self.audit_notes:
            lines.append("Audit notes:")
            for note in self.audit_notes:
                lines.append(f"- {note}")
        return "\n".join(lines)


__all__ = [
    "AuditResult",
    "FingerprintingAuditSuite",
    "ExternalTestbedIntegration",
    "PrivacyScorecard",
]
