"""PySide6 application shell with QtWebEngine and modernized chrome."""
from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QStatusBar
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineScript

from ghostline.logging_config import configure_logging, startup_banner
from ghostline.media.drm import enable_widevine, setup_widevine_environment
from ghostline.privacy.compatibility import StreamingCompatibilityAdvisor
from ghostline.privacy.injector import FingerprintInjector
from ghostline.privacy.rfp import unified_user_agent
from ghostline.ui.dashboard import PrivacyDashboard
from ghostline.ui.interceptor import MimeTypeFixInterceptor
from .components import NavigationBar, SettingsDialog


LOGGER = logging.getLogger(__name__)


class GhostlineWindow(QMainWindow):
    """Hardened browser shell with typed signals and status surfaces."""

    def __init__(self, home_url: str = "https://www.example.com") -> None:
        super().__init__()
        self.setWindowTitle("Ghostline Browser")
        self.resize(1280, 800)

        self.dashboard = PrivacyDashboard()
        self.compatibility_advisor = StreamingCompatibilityAdvisor()
        self.container_name = "default"
        container_badge = self.dashboard.ensure_container(self.container_name, template="research")

        self.web_view = QWebEngineView(self)
        # Enable Widevine profile settings (environment was set up in launch())
        self.widevine_enabled = enable_widevine(self.web_view.page().profile())

        # Set spoofed user agent on profile
        device = self.dashboard.device_randomizer.randomize(0)
        ua = unified_user_agent(platform=str(device['platform']) + " x86_64")
        self.web_view.page().profile().setHttpUserAgent(ua)
        LOGGER.info("user_agent_set", extra={"user_agent": ua, "platform": device['platform']})

        # Install request interceptor to fix MIME type issues
        interceptor = MimeTypeFixInterceptor()
        self.web_view.page().profile().setUrlRequestInterceptor(interceptor)

        # Install anti-fingerprinting script injection
        self.fp_injector = FingerprintInjector(self.dashboard, self.container_name)
        self._install_fingerprint_protection()

        self.web_view.load(QUrl(home_url))
        self.web_view.urlChanged.connect(self._update_address_bar)
        self.web_view.urlChanged.connect(self._update_security_state)
        self.web_view.loadFinished.connect(self._show_load_status)
        self._compatibility_note: str | None = None

        self.navigation_bar = NavigationBar(self)
        self.navigation_bar.navigate_requested.connect(self._on_navigate)
        self.navigation_bar.reload_requested.connect(self.web_view.reload)
        self.navigation_bar.home_requested.connect(lambda: self.web_view.load(QUrl(home_url)))
        self.navigation_bar.settings_requested.connect(self._open_settings)
        self.addToolBar(self.navigation_bar)
        self.navigation_bar.set_container_badge(
            self.container_name,
            container_badge.color,
            container_badge.isolation_badge,
        )

        self._build_menu()

        self.status_bar = QStatusBar(self)
        self.status_bar.hide()
        self.status_bar_label = QLabel("", self)
        self.status_bar.addPermanentWidget(self.status_bar_label)
        self.setStatusBar(self.status_bar)
        self.setCentralWidget(self.web_view)
        self._refresh_privacy_summary()

    def _on_navigate(self, target: str) -> None:
        if target == "back":
            self.web_view.back()
            return
        if target == "forward":
            self.web_view.forward()
            return

        url_text = target
        if "://" not in url_text:
            url_text = "https://" + url_text
        self.web_view.load(QUrl(url_text))

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        new_session_action = QAction("New Session", self)
        new_session_action.setShortcut(QKeySequence.New)
        new_session_action.triggered.connect(lambda: self.web_view.load(QUrl("about:blank")))
        file_menu.addAction(new_session_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = menu.addMenu("&View")
        view_menu.addAction("Reload", self.web_view.reload, QKeySequence.Refresh)
        view_menu.addAction("Back", lambda: self._on_navigate("back"), QKeySequence.Back)
        view_menu.addAction(
            "Forward", lambda: self._on_navigate("forward"), QKeySequence.Forward
        )

        tools_menu = menu.addMenu("&Tools")
        settings_action = QAction("Settings", self)
        settings_action.setShortcut(QKeySequence.Preferences)
        settings_action.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_action)

    def _update_address_bar(self, url: QUrl) -> None:
        self.navigation_bar.set_address(url.toString())

    def _update_security_state(self, url: QUrl) -> None:
        host = url.host() or None
        secure = url.scheme().lower().startswith("https")
        self.navigation_bar.update_security_state(secure, host)
        self.dashboard.record_navigation(self.container_name, url.toString())

        # Regenerate fingerprint protection for new origin
        self._install_fingerprint_protection()

        advisory = self.compatibility_advisor.advisory_for(host or "")
        if advisory:
            self._compatibility_note = (
                f"{advisory.host}: {advisory.symptom} (error {advisory.error_code}). "
                f"{advisory.remediation}"
            )
            LOGGER.info("compatibility_note", extra={"note": self._compatibility_note})
        else:
            self._compatibility_note = None
            LOGGER.info("compatibility_note", extra={"note": None})

    def _show_load_status(self, ok: bool) -> None:
        message = "Page loaded" if ok else "Failed to load page"
        LOGGER.info("navigation_status", extra={"success": ok, "status_message": message})
        self._refresh_privacy_summary()

    def _install_fingerprint_protection(self) -> None:
        """Install JavaScript that enforces anti-fingerprinting protections."""
        profile = self.web_view.page().profile()
        scripts = profile.scripts()

        # Remove old fingerprint script if exists
        for script in scripts.toList():
            if script.name() == "ghostline-fingerprint-protection":
                scripts.remove(script)

        # Generate script for current origin
        origin = self.dashboard._container_origins.get(self.container_name, "about:blank")
        script_source = self.fp_injector.generate_script(origin)

        # Create and configure script
        script = QWebEngineScript()
        script.setName("ghostline-fingerprint-protection")
        script.setSourceCode(script_source)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)

        scripts.insert(script)
        LOGGER.info("fingerprint_protection_installed", extra={"origin": origin, "container": self.container_name})

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.dashboard, self, container=self.container_name)
        if dialog.exec():
            container_badge = self.dashboard.container_ux.badge_for(self.container_name)
            if container_badge:
                self.navigation_bar.set_container_badge(
                    self.container_name,
                    container_badge.color,
                    container_badge.isolation_badge,
                )
            self._refresh_privacy_summary()

    def _refresh_privacy_summary(self) -> None:
        summary = self.dashboard.status_for_container(self.container_name)
        gating = self.dashboard.gating_snapshot(self.container_name)
        noise = self.dashboard.calibrated_noise_for(self.container_name)
        status_parts = [
            f"Mode: {summary['mode']}",
            f"Uniformity: {summary['uniformity']}",
            f"Entropy: {summary['entropy_bits']} bits",
            f"ECH: {'On' if summary['ech'] else 'Off'}",
            f"HTTPS-Only: {'On' if summary['https_only'] else 'Off'}",
            f"Tor: {'On' if summary['tor'] else 'Off'}",
            f"Origin: {summary['container_origin']}",
            f"Noise: canvas Δ{noise['canvas']['r']:.2f}/{noise['canvas']['g']:.2f}/{noise['canvas']['b']:.2f}",
            f"Audio Δ{noise['audio']:.2f}",
            "Gates: " + ", ".join(f"{api}={'✔' if allowed else '✖'}" for api, allowed in gating.items()),
        ]
        proxy = summary.get("proxy")
        if proxy:
            status_parts.append(f"Proxy: {proxy}")
        status_parts.append(f"Extensions: {len(summary.get('extensions', []))}")
        status_parts.append(
            f"Permissions: {len(summary.get('permissions', []))} ({summary.get('policy_mode', 'standard')})"
        )
        alerts = self.dashboard.sandbox_alerts()
        if alerts:
            status_parts.append(f"Sandbox alerts: {len(alerts)}")
        if self.widevine_enabled:
            status_parts.append("DRM: Widevine ready")
        else:
            status_parts.append("DRM: Widevine unavailable")
        if self._compatibility_note:
            status_parts.append(f"Compat: {self._compatibility_note}")
        status_text = "  |  ".join(status_parts)
        LOGGER.info("privacy_summary", extra={"summary": status_text})
        self.status_bar_label.clear()


def launch() -> None:
    configure_logging()
    startup_banner("ghostline")
    # Set up Widevine environment BEFORE QApplication initialization
    setup_widevine_environment()
    app = QApplication(sys.argv)
    window = GhostlineWindow()
    window.show()
    sys.exit(app.exec())
