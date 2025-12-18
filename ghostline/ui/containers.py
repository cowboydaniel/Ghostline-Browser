"""Container UX primitives for color-coding and policy bundles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


PALETTE = ["#4caf50", "#2196f3", "#ff9800", "#9c27b0", "#607d8b"]


@dataclass
class ContainerPolicyBundle:
    """Default policy bundle per container template."""

    name: str
    uniformity_preset: str
    tor_required: bool
    proxy_mode: str
    notes: List[str] = field(default_factory=list)


@dataclass
class ContainerBadge:
    name: str
    color: str
    policy: ContainerPolicyBundle
    isolation_badge: str


class ContainerUX:
    """Tracks container templates, badges, and color coding."""

    def __init__(self) -> None:
        self.templates = self._build_templates()
        self.badges: Dict[str, ContainerBadge] = {}
        self._palette_index = 0

    def _build_templates(self) -> Dict[str, ContainerPolicyBundle]:
        return {
            "balanced": ContainerPolicyBundle(
                name="balanced",
                uniformity_preset="balanced",
                tor_required=False,
                proxy_mode="standard",
                notes=["Fingerprint smoothing", "Proxy optional"],
            ),
            "research": ContainerPolicyBundle(
                name="research",
                uniformity_preset="strict",
                tor_required=True,
                proxy_mode="tor",
                notes=["Sensitive lookups isolated", "Strict capability mask"],
            ),
            "strict": ContainerPolicyBundle(
                name="strict",
                uniformity_preset="strict",
                tor_required=False,
                proxy_mode="hardened",
                notes=["Maximum uniformity", "WebGPU blocked"],
            ),
            "shopping": ContainerPolicyBundle(
                name="shopping",
                uniformity_preset="balanced",
                tor_required=False,
                proxy_mode="standard",
                notes=["Payment friendly", "Balanced entropy budget"],
            ),
            "banking": ContainerPolicyBundle(
                name="banking",
                uniformity_preset="strict",
                tor_required=False,
                proxy_mode="hardened",
                notes=["Certificates pinned", "Audio/WebGPU blocked"],
            ),
        }

    def _next_color(self) -> str:
        color = PALETTE[self._palette_index % len(PALETTE)]
        self._palette_index += 1
        return color

    def register_container(self, name: str, template: str) -> ContainerBadge:
        if template not in self.templates:
            raise ValueError(f"unknown-template:{template}")
        policy = self.templates[template]
        badge = ContainerBadge(
            name=name,
            color=self._next_color(),
            policy=policy,
            isolation_badge=f"isolated:{policy.uniformity_preset}",
        )
        self.badges[name] = badge
        return badge

    def badge_for(self, name: str) -> ContainerBadge | None:
        return self.badges.get(name)


__all__ = ["ContainerUX", "ContainerBadge", "ContainerPolicyBundle"]
