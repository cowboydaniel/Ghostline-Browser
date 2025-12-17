import os

import pytest

os.environ.setdefault("GHOSTLINE_FAKE_QT", "1")
from ghostline.media import drm


class DummySettings:
    def __init__(self):
        self.attributes = {}

    def setAttribute(self, key, value):
        self.attributes[key] = value


class DummyProfile:
    def __init__(self):
        self._settings = DummySettings()

    def settings(self):
        return self._settings


def test_find_widevine_library_prefers_custom_path(tmp_path):
    library = tmp_path / "libwidevinecdm.so"
    library.touch()

    discovered = drm.find_widevine_library([str(library)])
    assert discovered == str(library)


def test_enable_widevine_sets_flags_and_settings(tmp_path, monkeypatch):
    library = tmp_path / "libwidevinecdm.so"
    library.touch()
    profile = DummyProfile()

    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--foo")
    chosen = drm.enable_widevine(profile, library_path=str(library))

    assert chosen == str(library)
    assert profile._settings.attributes[drm.QWebEngineSettings.PluginsEnabled] is True
    assert profile._settings.attributes[drm.QWebEngineSettings.FullScreenSupportEnabled] is True
    assert profile._settings.attributes[drm.QWebEngineSettings.PlaybackRequiresUserGesture] is False

    flags = os.environ["QTWEBENGINE_CHROMIUM_FLAGS"]
    assert "--enable-widevine-cdm" in flags
    assert f"--widevine-path={library}" in flags
    assert flags.startswith("--foo")


def test_enable_widevine_is_idempotent(tmp_path, monkeypatch):
    library = tmp_path / "libwidevinecdm.so"
    library.touch()
    profile = DummyProfile()

    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "")
    drm.enable_widevine(profile, library_path=str(library))
    flags_first = os.environ["QTWEBENGINE_CHROMIUM_FLAGS"]
    drm.enable_widevine(profile, library_path=str(library))
    flags_second = os.environ["QTWEBENGINE_CHROMIUM_FLAGS"]

    assert flags_first == flags_second
