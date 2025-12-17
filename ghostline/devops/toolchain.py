"""Developer experience helpers for hermetic environments and telemetry guardrails."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass
class ToolchainConfig:
    python_version: str
    qt_version: str
    frozen_dependencies: Dict[str, str]
    telemetry_enabled: bool = False

    def to_lockfile(self, path: Path) -> None:
        payload = {
            "python": self.python_version,
            "qt": self.qt_version,
            "deps": self.frozen_dependencies,
            "telemetry": self.telemetry_enabled,
        }
        path.write_text(json.dumps(payload, sort_keys=True, indent=2))

    def digest(self) -> str:
        raw = json.dumps(self.frozen_dependencies, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()


def privacy_preserving_default() -> ToolchainConfig:
    return ToolchainConfig(
        python_version="3.11",
        qt_version="6.6",
        frozen_dependencies={"PySide6": ">=6.6", "httpx": ">=0.25"},
        telemetry_enabled=False,
    )
