"""Release engineering and staged rollout helpers for Phase 5."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from ghostline.networking.hygiene import ProxyLeakSuite
from ghostline.networking.tor import TorController
from ghostline.privacy.audit import ExternalTestbedIntegration, FingerprintingAuditSuite


@dataclass
class PrivacyCIOrchestrator:
    """Runs proxy leak, fingerprinting, and Tor integration suites."""

    proxy_suite: ProxyLeakSuite = field(default_factory=ProxyLeakSuite)
    audit_suite: FingerprintingAuditSuite = field(default_factory=FingerprintingAuditSuite)
    testbed: ExternalTestbedIntegration = field(default_factory=ExternalTestbedIntegration)
    tor_controller: TorController = field(default_factory=TorController)
    regressions: List[str] = field(default_factory=list)
    last_diff: Dict[str, int] = field(default_factory=dict)

    def run(self, uniformity_manager, containers: List[str], proxy_summary: Dict[str, bool]) -> Dict[str, object]:
        leak_results = self.proxy_suite.run(proxy_summary)
        audit_result = self.audit_suite.compare_uniformity(uniformity_manager, containers)
        tor_health = self.tor_controller.health_summary()

        if not audit_result.consistent:
            self.regressions.append("uniformity-regression")
        if not all(leak_results.values()):
            self.regressions.append("proxy-leak")

        if self.testbed.snapshots:
            self.last_diff = self.testbed.latest_diff()

        return {
            "leaks": leak_results,
            "uniformity_consistent": audit_result.consistent,
            "notes": audit_result.notes,
            "tor": tor_health,
            "regressions": list(self.regressions),
            "diff": dict(self.last_diff),
        }


@dataclass
class ReproducibilityDashboard:
    """Compares artifact digests across release trains and surfaces variance alerts."""

    artifacts: Dict[str, Dict[str, str]] = field(default_factory=dict)
    variance_alerts: List[str] = field(default_factory=list)

    def record_artifact(self, train: str, name: str, digest: str) -> None:
        self.artifacts.setdefault(name, {})[train] = digest
        self._check_variance(name)

    def _check_variance(self, name: str) -> None:
        digests = set(self.artifacts.get(name, {}).values())
        if len(digests) > 1:
            alert = f"variance:{name}:{len(digests)}"
            if alert not in self.variance_alerts:
                self.variance_alerts.append(alert)

    def dashboard(self) -> Dict[str, Dict[str, str]]:
        return {name: versions.copy() for name, versions in self.artifacts.items()}


@dataclass
class FeatureFlag:
    name: str
    enabled: bool = False
    cohort: str = "stable"


class RolloutController:
    """Manages kill switches, feature flags, and canary cohorts."""

    def __init__(self) -> None:
        self.flags: Dict[str, FeatureFlag] = {}
        self.kill_switches: Set[str] = set()
        self.canary_cohorts: Dict[str, str] = {}

    def register_feature(self, name: str, cohort: str = "stable") -> None:
        self.flags[name] = FeatureFlag(name=name, enabled=False, cohort=cohort)

    def enable_feature(self, name: str, cohort: str | None = None) -> None:
        flag = self.flags.get(name)
        if flag is None:
            flag = FeatureFlag(name=name)
        if cohort:
            flag.cohort = cohort
        flag.enabled = True
        self.flags[name] = flag

    def disable_feature(self, name: str) -> None:
        if name in self.flags:
            self.flags[name].enabled = False

    def kill_switch(self, name: str) -> None:
        self.kill_switches.add(name)

    def assign_cohort(self, user_id: str, cohort: str) -> None:
        self.canary_cohorts[user_id] = cohort

    def evaluate(self, user_id: str, feature: str) -> bool:
        if feature in self.kill_switches:
            return False
        flag = self.flags.get(feature)
        if not flag or not flag.enabled:
            return False
        cohort = self.canary_cohorts.get(user_id, "stable")
        return cohort == flag.cohort or flag.cohort == "stable"


__all__ = [
    "FeatureFlag",
    "PrivacyCIOrchestrator",
    "ReproducibilityDashboard",
    "RolloutController",
]
