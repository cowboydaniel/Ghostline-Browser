"""DRM helpers for enabling Widevine/EME playback in QtWebEngine."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

_USE_FAKE_QT = os.environ.get("GHOSTLINE_FAKE_QT", "0") == "1"

if not _USE_FAKE_QT:
    from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
else:
    class QWebEngineSettings:  # type: ignore[override]
        PluginsEnabled = "PluginsEnabled"
        FullScreenSupportEnabled = "FullScreenSupportEnabled"
        PlaybackRequiresUserGesture = "PlaybackRequiresUserGesture"

    class QWebEngineProfile:  # type: ignore[override]
        def __init__(self) -> None:
            self._settings = None

        def settings(self):  # pragma: no cover - only used in fake mode
            return self._settings

# Common locations where Widevine may be installed by Chrome/Chromium packages.
_DEFAULT_WIDEVINE_PATHS = (
    "/opt/google/chrome/WidevineCdm/_platform_specific/linux_x64/libwidevinecdm.so",
    "/usr/lib/chromium/WidevineCdm/_platform_specific/linux_x64/libwidevinecdm.so",
    "/usr/lib64/chromium/WidevineCdm/_platform_specific/linux_x64/libwidevinecdm.so",
)

_DEFAULT_SEARCH_ROOTS = (
    Path.home(),
    Path("/usr/lib"),
    Path("/usr/lib64"),
    Path("/usr/local/lib"),
    Path("/opt"),
    Path("/var/lib/snapd"),
)


def find_widevine_library(extra_paths: Iterable[str] | None = None) -> Optional[str]:
    """Return the first existing Widevine library path from known or provided hints.

    Falls back to a shallow filesystem search so users with browser-managed
    installs (e.g., Firefox's GMP plugin) do not have to manually locate the
    library.
    """

    hints = list(extra_paths or []) + list(_DEFAULT_WIDEVINE_PATHS)
    for candidate in hints:
        if candidate and Path(candidate).exists():
            return str(Path(candidate))

    search_roots = os.environ.get("WIDEVINE_SEARCH_ROOTS")
    if search_roots:
        roots = [Path(p) for p in search_roots.split(os.pathsep) if p]
    else:
        roots = [root for root in _DEFAULT_SEARCH_ROOTS if root.exists()]

    for root in roots:
        try:
            for match in root.rglob("libwidevinecdm.so"):
                return str(match)
        except PermissionError:
            continue
    return None


def _append_flag(flags: str, new_flag: str) -> str:
    if not flags:
        return new_flag
    if new_flag in flags:
        return flags
    return f"{flags} {new_flag}".strip()


def setup_widevine_environment(extra_paths: Iterable[str] | None = None) -> Optional[str]:
    """Set up Widevine environment variables BEFORE QtWebEngine initialization.

    This must be called before QApplication is created. Returns the library path
    if Widevine was found and configured.
    """
    import logging

    logger = logging.getLogger(__name__)
    library = find_widevine_library(extra_paths)

    if library:
        flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
        flags = _append_flag(flags, "--enable-widevine-cdm")
        flags = _append_flag(flags, f"--widevine-path={library}")
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = flags
        logger.info("widevine_enabled", extra={"library_path": library})
    else:
        logger.info("widevine_unavailable", extra={
            "message": "Widevine CDM not found on system. Install google-chrome or chromium to enable DRM playback.",
            "search_paths": str(_DEFAULT_WIDEVINE_PATHS)
        })

    return library


def enable_widevine(profile: QWebEngineProfile) -> bool:
    """Enable Widevine DRM profile settings.

    Should be called after setup_widevine_environment() and after QWebEngineProfile
    is created. Configures profile-level settings needed for DRM playback.
    """

    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)

    # Check if Widevine was configured via environment variables
    return "--enable-widevine-cdm" in os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
