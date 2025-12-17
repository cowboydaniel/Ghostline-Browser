"""Uniformity profiles and high-entropy API gating."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


HIGH_ENTROPY_APIS = {"webgl", "webgpu", "audiocontext", "gamepad"}


@dataclass
class FontPack:
    """Locale-aware font packs with per-site overrides."""

    name: str
    locales: Dict[str, List[str]]
    site_overrides: Dict[str, List[str]] = field(default_factory=dict)

    def fonts_for(self, locale: str, site: str | None = None) -> List[str]:
        if site and site in self.site_overrides:
            return self.site_overrides[site]
        return self.locales.get(locale, self.locales.get("default", []))

    def override_for_site(self, site: str, fonts: List[str]) -> None:
        self.site_overrides[site] = fonts


@dataclass
class UniformityProfile:
    """Represents a set of capability masks and font normalization."""

    name: str
    capability_mask: Dict[str, bool]
    font_pack: FontPack
    strict_mode: bool = False

    def gate_api(self, api: str) -> bool:
        if self.strict_mode and api in HIGH_ENTROPY_APIS:
            return False
        return self.capability_mask.get(api, True)


class UniformityManager:
    """Manages per-container uniformity presets and capability gating."""

    def __init__(self) -> None:
        self.presets = self._build_presets()
        self.container_profiles: Dict[str, UniformityProfile] = {}

    def _build_presets(self) -> Dict[str, UniformityProfile]:
        base_fonts = FontPack(
            name="baseline",
            locales={
                "default": ["Inter", "Noto Sans", "DejaVu Sans"],
                "en-US": ["Inter", "Roboto", "Noto Sans"],
                "fr-FR": ["Inter", "Noto Sans", "Liberation Sans"],
            },
        )
        strict_mask = {api: False for api in HIGH_ENTROPY_APIS}
        balanced_mask = {
            "webgl": True,
            "webgpu": False,
            "audiocontext": True,
            "gamepad": True,
        }
        compat_mask = {api: True for api in HIGH_ENTROPY_APIS}

        return {
            "strict": UniformityProfile(
                name="strict",
                capability_mask=strict_mask,
                font_pack=base_fonts,
                strict_mode=True,
            ),
            "balanced": UniformityProfile(
                name="balanced",
                capability_mask=balanced_mask,
                font_pack=base_fonts,
                strict_mode=False,
            ),
            "compat": UniformityProfile(
                name="compat",
                capability_mask=compat_mask,
                font_pack=base_fonts,
                strict_mode=False,
            ),
        }

    def apply_preset(self, container: str, preset: str, locale: str = "default") -> UniformityProfile:
        if preset not in self.presets:
            raise ValueError(f"unknown-preset:{preset}")
        profile = self.presets[preset]
        # Clone a profile so per-container overrides don't leak
        cloned = UniformityProfile(
            name=profile.name,
            capability_mask=dict(profile.capability_mask),
            font_pack=FontPack(profile.font_pack.name, dict(profile.font_pack.locales), dict(profile.font_pack.site_overrides)),
            strict_mode=profile.strict_mode,
        )
        # Ensure locale defaults exist
        cloned.font_pack.locales.setdefault(locale, cloned.font_pack.locales.get("default", []))
        self.container_profiles[container] = cloned
        return cloned

    def profile_for(self, container: str) -> UniformityProfile:
        return self.container_profiles.get(container, self.presets["compat"])

    def fonts_for(self, container: str, locale: str, site: str | None = None) -> List[str]:
        profile = self.profile_for(container)
        return profile.font_pack.fonts_for(locale, site)

    def gate_api(self, container: str, api: str) -> bool:
        profile = self.profile_for(container)
        return profile.gate_api(api)

    def set_site_override(self, container: str, site: str, fonts: List[str]) -> None:
        profile = self.profile_for(container)
        profile.font_pack.override_for_site(site, fonts)


__all__ = ["FontPack", "UniformityProfile", "UniformityManager", "HIGH_ENTROPY_APIS"]
