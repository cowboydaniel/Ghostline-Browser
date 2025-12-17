"""Community publishing helpers for threat models, changelogs, and compatibility matrices."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ReleaseCommunication:
    version: str
    threat_models: List[str]
    architecture_docs: List[str]
    changelog: str
    governance: str


class ReleaseCommunicator:
    def __init__(self) -> None:
        self.changelogs: Dict[str, ReleaseCommunication] = {}
        self.test_harnesses: List[str] = []
        self.compatibility_matrix: Dict[str, Dict[str, str]] = {}

    def publish_release(self, version: str, threat_models: List[str], architecture_docs: List[str], mitigations: List[str]) -> ReleaseCommunication:
        changelog = "\n".join(f"- {entry}" for entry in mitigations)
        communication = ReleaseCommunication(
            version=version,
            threat_models=threat_models,
            architecture_docs=architecture_docs,
            changelog=changelog,
            governance="contributions welcome",
        )
        self.changelogs[version] = communication
        return communication

    def record_test_harness(self, name: str) -> None:
        if name not in self.test_harnesses:
            self.test_harnesses.append(name)

    def update_matrix(self, category: str, item: str, status: str) -> None:
        self.compatibility_matrix.setdefault(category, {})[item] = status


__all__ = ["ReleaseCommunication", "ReleaseCommunicator"]
