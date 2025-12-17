"""Entropy budgeting, device class randomization, and calibrated noise."""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class EntropyBudget:
    """Tracks cross-API entropy consumption with violation surfacing."""

    limit_bits: int = 16
    usage: Dict[str, int] = field(default_factory=dict)
    devtools_events: List[str] = field(default_factory=list)
    telemetry_events: List[str] = field(default_factory=list)

    def consume(self, api: str, bits: int) -> bool:
        current = self.usage.get(api, 0)
        self.usage[api] = current + bits
        total = sum(self.usage.values())
        self.devtools_events.append(f"consume:{api}:{bits}bits:total={total}")
        if total > self.limit_bits:
            message = f"budget-exceeded:{api}:{total}/{self.limit_bits}"
            self.devtools_events.append(message)
            self.telemetry_events.append(message)
            return False
        return True

    def reset(self) -> None:
        self.usage.clear()
        self.devtools_events.clear()
        self.telemetry_events.clear()

    def total_bits(self) -> int:
        return sum(self.usage.values())


@dataclass
class DeviceRandomizer:
    """Randomizes device class attributes with stability windows."""

    seed: str = "ghostline-device"
    stability_window: int = 3
    randomized: Dict[int, Dict[str, str | int]] = field(default_factory=dict)

    # Common screen resolutions for bucketing
    SCREEN_BUCKETS = [
        {"width": 1920, "height": 1080, "availHeight": 1040},  # Full HD
        {"width": 1366, "height": 768, "availHeight": 728},    # HD
        {"width": 1440, "height": 900, "availHeight": 860},    # WXGA+
        {"width": 1536, "height": 864, "availHeight": 824},    # Common laptop
        {"width": 2560, "height": 1440, "availHeight": 1400},  # QHD
    ]

    def _bucket(self, window_id: int) -> int:
        return window_id // self.stability_window

    def randomize(self, window_id: int) -> Dict[str, str | int]:
        bucket = self._bucket(window_id)
        if bucket not in self.randomized:
            material = f"{self.seed}:{bucket}".encode()
            digest = hashlib.sha256(material).hexdigest()
            rng = random.Random(int(digest[:8], 16))
            self.randomized[bucket] = {
                "gpu": f"Ghostline GPU Class {rng.randint(1, 5)}",
                "memory_gb": rng.choice([4, 8, 16]),
                "platform": rng.choice(["Linux", "Windows", "macOS"]),
            }
        return self.randomized[bucket]

    def screen_dimensions(self, window_id: int) -> Dict[str, int]:
        """Get randomized screen dimensions for a given window bucket.

        Args:
            window_id: Window identifier for bucket calculation

        Returns:
            Dictionary with screen dimension properties
        """
        bucket = self._bucket(window_id)
        material = f"{self.seed}:screen:{bucket}".encode()
        digest = hashlib.sha256(material).hexdigest()
        rng = random.Random(int(digest[:8], 16))

        # Pick a random screen bucket
        screen = rng.choice(self.SCREEN_BUCKETS).copy()

        # Add additional properties
        screen['availWidth'] = screen['width']
        screen['colorDepth'] = 24
        screen['pixelDepth'] = 24

        return screen


@dataclass
class NoiseCalibrator:
    """Generates deterministic canvas and audio noise with calibrated amplitude."""

    amplitude: float = 0.2
    seed_secret: str = "ghostline-noise"

    def _rng_for_origin(self, origin: str) -> random.Random:
        digest = hashlib.sha256(f"{origin}:{self.seed_secret}".encode()).hexdigest()
        return random.Random(int(digest[:8], 16))

    def canvas_noise(self, origin: str) -> Dict[str, float]:
        rng = self._rng_for_origin(origin)
        return {
            "r": rng.uniform(-self.amplitude, self.amplitude),
            "g": rng.uniform(-self.amplitude, self.amplitude),
            "b": rng.uniform(-self.amplitude, self.amplitude),
            "a": rng.uniform(-(self.amplitude / 2), self.amplitude / 2),
        }

    def audio_noise(self, origin: str) -> float:
        rng = self._rng_for_origin(origin)
        return rng.uniform(-(self.amplitude / 2), self.amplitude / 2)


__all__ = ["EntropyBudget", "DeviceRandomizer", "NoiseCalibrator"]
