"""Resisting Fingerprinting (RFP) helpers for timers, canvas, and UA."""
from __future__ import annotations

import hashlib
import random
import time
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import Dict


TIMER_GRANULARITY_MS = 100


def rounded_time(now: float | None = None) -> float:
    reference = now if now is not None else time.time()
    bucket_steps = round(reference / 0.1)
    bucket = (bucket_steps % 10) / 10
    return bucket


@dataclass
class CanvasNoiseInjector:
    """Generates deterministic per-origin noise for canvas-like APIs."""

    seed_secret: str = "ghostline-rfp-seed"

    def noise_for_origin(self, origin: str) -> Dict[str, float]:
        material = f"{origin}-{self.seed_secret}".encode()
        digest = hashlib.sha256(material).hexdigest()
        random.seed(int(digest[:8], 16))
        return {
            "r": random.uniform(-0.5, 0.5),
            "g": random.uniform(-0.5, 0.5),
            "b": random.uniform(-0.5, 0.5),
            "a": random.uniform(-0.1, 0.1),
        }


def unified_user_agent(platform: str = "Linux x86_64") -> str:
    return f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Ghostline/1.0"
