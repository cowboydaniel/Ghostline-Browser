"""Incident response, monitoring, and on-call coordination primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RedTeamExercise:
    focus: str
    outcome: Optional[str] = None
    findings: List[str] = field(default_factory=list)


@dataclass
class RedTeamProgram:
    cadence: str = "quarterly"
    exercises: List[RedTeamExercise] = field(default_factory=list)

    def schedule_exercise(self, focus: str) -> RedTeamExercise:
        exercise = RedTeamExercise(focus=focus)
        self.exercises.append(exercise)
        return exercise

    def record_result(self, exercise: RedTeamExercise, outcome: str, findings: List[str]) -> None:
        exercise.outcome = outcome
        exercise.findings.extend(findings)

    @property
    def open_findings(self) -> List[str]:
        results: List[str] = []
        for exercise in self.exercises:
            results.extend(exercise.findings)
        return results


@dataclass
class CrashTelemetryPipeline:
    """Client-side redaction, sampling, and privacy budget enforcement."""

    sample_rate: float = 0.5
    budget: int = 100
    uploads: List[Dict[str, str]] = field(default_factory=list)
    redaction_keys: List[str] = field(default_factory=lambda: ["email", "ip", "cookies"])

    def sanitize(self, report: Dict[str, str]) -> Dict[str, str]:
        sanitized = {k: v for k, v in report.items() if k not in self.redaction_keys}
        sanitized["redacted_fields"] = [k for k in report if k in self.redaction_keys]
        return sanitized

    def submit(self, report: Dict[str, str]) -> bool:
        if self.budget <= 0:
            return False
        # deterministic sampling using signature hash for predictability in tests
        signature = report.get("signature", "")
        if signature and (hash(signature) % 100) / 100 > self.sample_rate:
            return False
        self.uploads.append(report)
        self.budget -= 1
        return True


@dataclass
class OnCallRotation:
    """Maintains on-call rotations, runbooks, and playbooks for incidents."""

    rotation: List[str] = field(default_factory=lambda: ["alice", "bob", "carol"])
    runbooks: Dict[str, str] = field(default_factory=dict)
    playbooks: Dict[str, List[str]] = field(default_factory=dict)
    _current_index: int = 0

    def current_oncall(self) -> str:
        return self.rotation[self._current_index % len(self.rotation)]

    def next_oncall(self) -> str:
        self._current_index = (self._current_index + 1) % len(self.rotation)
        return self.current_oncall()

    def add_runbook(self, incident: str, steps: str) -> None:
        self.runbooks[incident] = steps

    def add_playbook(self, incident: str, actions: List[str]) -> None:
        self.playbooks[incident] = actions


__all__ = ["CrashTelemetryPipeline", "OnCallRotation", "RedTeamExercise", "RedTeamProgram"]
