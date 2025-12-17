"""Tor mode controls with circuit isolation and pluggable transports."""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TorCircuit:
    container: str
    guard_node: str
    healthy: bool = True
    fingerprint_errors: int = 0


class TorController:
    """Tracks Tor bootstrap state and per-container isolation."""

    def __init__(self) -> None:
        self.enabled: bool = False
        self.bootstrap_steps: List[str] = ["starting", "connecting", "handshaking", "done"]
        self.progress_index: int = 0
        self.circuits: Dict[str, TorCircuit] = {}
        self.guard_nodes = itertools.cycle(["guard-a", "guard-b", "guard-c"])
        self.pluggable_transports: List[str] = ["obfs4", "snowflake"]
        self.active_transport: Optional[str] = None

    def enable(self, transport_preference: Optional[str] = None) -> None:
        self.enabled = True
        self.progress_index = min(self.progress_index + 1, len(self.bootstrap_steps) - 1)
        self.active_transport = self._select_transport(transport_preference)

    def _select_transport(self, preference: Optional[str]) -> Optional[str]:
        if preference and preference in self.pluggable_transports:
            return preference
        return self.pluggable_transports[0]

    def bootstrap_status(self) -> str:
        return self.bootstrap_steps[self.progress_index]

    def isolate_stream(self, container: str) -> TorCircuit:
        if container not in self.circuits:
            self.circuits[container] = TorCircuit(container=container, guard_node=next(self.guard_nodes))
        return self.circuits[container]

    def mark_fingerprint_error(self, container: str) -> TorCircuit:
        circuit = self.isolate_stream(container)
        new_circuit = TorCircuit(
            container=container,
            guard_node=next(self.guard_nodes),
            healthy=False,
            fingerprint_errors=circuit.fingerprint_errors + 1,
        )
        self.circuits[container] = new_circuit
        return new_circuit

    def health_summary(self) -> Dict[str, bool]:
        return {name: circuit.healthy for name, circuit in self.circuits.items()}


__all__ = ["TorController", "TorCircuit"]
