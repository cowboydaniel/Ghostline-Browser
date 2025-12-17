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


def enable_widevine(profile: QWebEngineProfile, library_path: Optional[str] = None) -> Optional[str]:
    """Enable Widevine DRM for the given profile if a library is available.

    Returns the library path when successfully configured so callers can surface
    status to users. The function is idempotent and safe to call multiple times.
    """

    library = library_path or find_widevine_library()

    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)

    if library:
        flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
        flags = _append_flag(flags, "--enable-widevine-cdm")
        flags = _append_flag(flags, f"--widevine-path={library}")
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = flags
    return library
