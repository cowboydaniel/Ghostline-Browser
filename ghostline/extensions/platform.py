"""Extension platform with store, policies, and sandbox monitoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


SENSITIVE_APIS = {"nativeMessaging", "clipboard", "fileSystem", "processes"}


@dataclass
class ExtensionManifest:
    """Manifest representation with permissions and declared capabilities."""

    name: str
    version: str
    permissions: List[str]
    capabilities: Dict[str, bool] = field(default_factory=dict)
    reference_hash: str | None = None


@dataclass
class ExtensionPackage:
    """Published extension artifact with provenance and review notes."""

    identifier: str
    manifest: ExtensionManifest
    signature: str
    build_hash: str
    provenance: str
    review_notes: List[str] = field(default_factory=list)

    @property
    def signed(self) -> bool:
        return bool(self.signature)


@dataclass
class AnalysisFinding:
    code: str
    severity: str
    detail: str


class StaticAnalyzer:
    """Performs mandatory static analysis before publishing."""

    def analyze(self, manifest: ExtensionManifest) -> List[AnalysisFinding]:
        findings: List[AnalysisFinding] = []
        for perm in manifest.permissions:
            if perm in SENSITIVE_APIS:
                findings.append(
                    AnalysisFinding(
                        code="sensitive-permission",
                        severity="high",
                        detail=f"Permission {perm} gated by default",
                    )
                )
        if not manifest.name or not manifest.version:
            findings.append(
                AnalysisFinding(
                    code="invalid-manifest", severity="critical", detail="Missing metadata"
                )
            )
        return findings


class PermissionReview:
    """Approves or rejects based on manifest permissions."""

    def review(self, manifest: ExtensionManifest) -> Tuple[bool, List[str]]:
        denied = [perm for perm in manifest.permissions if perm in SENSITIVE_APIS]
        notes = [f"{perm} requires sandboxing" for perm in denied]
        # Sensitive permissions are allowed when gated, but they must be annotated.
        return (True, notes)


class ReproducibleBuildVerifier:
    """Validates reproducible build provenance via hash comparison."""

    def verify(self, package: ExtensionPackage) -> bool:
        if not package.manifest.reference_hash:
            return False
        return package.build_hash == package.manifest.reference_hash


class ExtensionStore:
    """Curated store enforcing signing, analysis, and reproducible builds."""

    def __init__(self) -> None:
        self.analyzer = StaticAnalyzer()
        self.reviewer = PermissionReview()
        self.verifier = ReproducibleBuildVerifier()
        self.extensions: Dict[str, ExtensionPackage] = {}
        self.analysis_findings: Dict[str, List[AnalysisFinding]] = {}

    def publish(self, package: ExtensionPackage) -> None:
        if not package.signed:
            raise ValueError("unsigned-extension")
        findings = self.analyzer.analyze(package.manifest)
        self.analysis_findings[package.identifier] = findings
        if any(f.severity == "critical" for f in findings):
            raise ValueError("static-analysis-blocked")
        approved, notes = self.reviewer.review(package.manifest)
        package.review_notes.extend(notes)
        if not approved:
            raise ValueError("permission-review-denied")
        if not self.verifier.verify(package):
            raise ValueError("non-reproducible-build")
        self.extensions[package.identifier] = package

    def get(self, identifier: str) -> ExtensionPackage | None:
        return self.extensions.get(identifier)

    def findings_for(self, identifier: str) -> List[AnalysisFinding]:
        return self.analysis_findings.get(identifier, [])


class ManifestGatekeeper:
    """Applies manifest-level capability gating for sensitive APIs."""

    def gate(self, manifest: ExtensionManifest) -> Dict[str, bool]:
        gated: Dict[str, bool] = {}
        for perm in manifest.permissions:
            gated[perm] = perm not in SENSITIVE_APIS
        return gated


@dataclass
class ExtensionPolicy:
    allowlist: Set[str] = field(default_factory=set)
    denylist: Set[str] = field(default_factory=set)
    gated_permissions: Dict[str, Dict[str, bool]] = field(default_factory=dict)

    def clone(self) -> "ExtensionPolicy":
        return ExtensionPolicy(
            allowlist=set(self.allowlist),
            denylist=set(self.denylist),
            gated_permissions={k: dict(v) for k, v in self.gated_permissions.items()},
        )


class ExtensionManager:
    """Tracks per-container allowlists/denylists and gating decisions."""

    def __init__(self, gatekeeper: ManifestGatekeeper) -> None:
        self.gatekeeper = gatekeeper
        self.policies: Dict[str, ExtensionPolicy] = {}
        self.active_extensions: Dict[str, List[str]] = {}

    def allow_extension(self, container: str, extension_id: str) -> None:
        policy = self.policies.setdefault(container, ExtensionPolicy())
        policy.allowlist.add(extension_id)
        policy.denylist.discard(extension_id)

    def deny_extension(self, container: str, extension_id: str) -> None:
        policy = self.policies.setdefault(container, ExtensionPolicy())
        policy.denylist.add(extension_id)
        policy.allowlist.discard(extension_id)
        if extension_id in self.active_extensions.get(container, []):
            self.active_extensions[container].remove(extension_id)

    def install(self, container: str, package: ExtensionPackage) -> None:
        policy = self.policies.setdefault(container, ExtensionPolicy())
        if package.identifier in policy.denylist:
            raise ValueError("extension-denied")
        if policy.allowlist and package.identifier not in policy.allowlist:
            raise ValueError("extension-not-allowlisted")
        policy.gated_permissions[package.identifier] = self.gatekeeper.gate(package.manifest)
        self.active_extensions.setdefault(container, [])
        if package.identifier not in self.active_extensions[container]:
            self.active_extensions[container].append(package.identifier)

    def clone_policy(self, source: str, target: str) -> None:
        if source not in self.policies:
            self.policies[target] = ExtensionPolicy()
            return
        self.policies[target] = self.policies[source].clone()
        self.active_extensions[target] = list(self.active_extensions.get(source, []))

    def is_allowed(self, container: str, extension_id: str) -> bool:
        policy = self.policies.get(container, ExtensionPolicy())
        if policy.allowlist and extension_id not in policy.allowlist:
            return False
        return extension_id not in policy.denylist

    def gated_permissions(self, container: str, extension_id: str) -> Dict[str, bool]:
        policy = self.policies.get(container, ExtensionPolicy())
        return policy.gated_permissions.get(extension_id, {})

    def installed_for(self, container: str) -> List[str]:
        return self.active_extensions.get(container, [])


@dataclass
class ResourceBudget:
    cpu_ms: int = 50
    memory_mb: int = 128
    network_kb: int = 512


class ExtensionSandboxMonitor:
    """Tracks resource budgets and emits anomaly alerts."""

    def __init__(self) -> None:
        self.budgets: Dict[str, ResourceBudget] = {}
        self.usage: Dict[str, ResourceBudget] = {}
        self.alerts: List[str] = []

    def set_budget(self, extension_id: str, budget: ResourceBudget) -> None:
        self.budgets[extension_id] = budget
        self.usage.setdefault(extension_id, ResourceBudget(0, 0, 0))

    def record_usage(self, extension_id: str, cpu_ms: int, memory_mb: int, network_kb: int) -> None:
        usage = self.usage.setdefault(extension_id, ResourceBudget(0, 0, 0))
        usage.cpu_ms += cpu_ms
        usage.memory_mb += memory_mb
        usage.network_kb += network_kb
        budget = self.budgets.get(extension_id, ResourceBudget())
        if (
            usage.cpu_ms > budget.cpu_ms
            or usage.memory_mb > budget.memory_mb
            or usage.network_kb > budget.network_kb
        ):
            self.alerts.append(f"anomaly:{extension_id}")


class ExtensionPlatform:
    """High-level integration point for the browser to manage extensions."""

    def __init__(self) -> None:
        self.store = ExtensionStore()
        self.gatekeeper = ManifestGatekeeper()
        self.manager = ExtensionManager(self.gatekeeper)
        self.sandbox = ExtensionSandboxMonitor()

    def publish(self, package: ExtensionPackage) -> None:
        self.store.publish(package)

    def enable_for_container(self, container: str, extension_id: str) -> None:
        package = self.store.get(extension_id)
        if not package:
            raise ValueError("unknown-extension")
        self.manager.install(container, package)
        self.sandbox.set_budget(extension_id, ResourceBudget())

    def clone_container_policy(self, source: str, target: str) -> None:
        self.manager.clone_policy(source, target)

    def container_extensions(self, container: str) -> List[str]:
        return self.manager.installed_for(container)


__all__ = [
    "AnalysisFinding",
    "ExtensionManifest",
    "ExtensionPackage",
    "ExtensionPlatform",
    "ExtensionManager",
    "ExtensionPolicy",
    "ExtensionSandboxMonitor",
    "ExtensionStore",
    "ManifestGatekeeper",
    "PermissionReview",
    "ReproducibleBuildVerifier",
    "ResourceBudget",
    "SENSITIVE_APIS",
    "StaticAnalyzer",
]
