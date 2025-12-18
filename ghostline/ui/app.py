"""PySide6 application shell with QtWebEngine and modernized chrome."""
from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QStatusBar, QTabWidget, QWidget, QPushButton
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


class BrowserTab:
    """Wrapper for a web view tab with associated metadata."""

    def __init__(self, web_view: QWebEngineView, container_name: str) -> None:
        self.web_view = web_view
        self.container_name = container_name
        self.title = "New Tab"


class GhostlineWindow(QMainWindow):
    """Hardened browser shell with typed signals and status surfaces."""

    def __init__(self, home_url: str = "https://www.example.com") -> None:
        super().__init__()
        self.setWindowTitle("Ghostline Browser")
        self.resize(1280, 800)

        self.dashboard = PrivacyDashboard()
        self.compatibility_advisor = StreamingCompatibilityAdvisor()
        self.home_url = home_url
        self._compatibility_note: str | None = None

        # Initialize shared profile for all tabs
        self.default_container_name = "default"
        container_badge = self.dashboard.ensure_container(self.default_container_name, template="research")

        # Create a temporary web view to set up the shared profile
        temp_view = QWebEngineView(self)
        self.shared_profile = temp_view.page().profile()

        # Enable Widevine profile settings (environment was set up in launch())
        self.widevine_enabled = enable_widevine(self.shared_profile)

        # Set spoofed user agent on profile
        device = self.dashboard.device_randomizer.randomize(0)
        ua = unified_user_agent(platform=str(device['platform']) + " x86_64")
        self.shared_profile.setHttpUserAgent(ua)
        LOGGER.info("user_agent_set", extra={"user_agent": ua, "platform": device['platform']})

        # Install request interceptor to fix MIME type issues
        interceptor = MimeTypeFixInterceptor()
        self.shared_profile.setUrlRequestInterceptor(interceptor)

        # Initialize tab management
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_switched)

        # Add "+" button to create new tabs
        new_tab_btn = QPushButton("+", self)
        new_tab_btn.setMaximumWidth(30)
        new_tab_btn.clicked.connect(lambda: self._new_tab())
        self.tab_widget.setCornerWidget(new_tab_btn)

        self.tabs: dict[int, BrowserTab] = {}
        self.tab_counter = 0
        self.fp_injectors: dict[int, FingerprintInjector] = {}

        # Install anti-fingerprinting script injection for default container
        self.fp_injectors[self.default_container_name] = FingerprintInjector(self.dashboard, self.default_container_name)

        self.navigation_bar = NavigationBar(self)
        self.navigation_bar.navigate_requested.connect(self._on_navigate)
        self.navigation_bar.reload_requested.connect(self._reload_current_tab)
        self.navigation_bar.home_requested.connect(self._home_current_tab)
        self.navigation_bar.settings_requested.connect(self._open_settings)
        self.addToolBar(self.navigation_bar)
        self.navigation_bar.set_container_badge(
            self.default_container_name,
            container_badge.color,
            container_badge.isolation_badge,
        )

        self._build_menu()

        self.status_bar = QStatusBar(self)
        self.status_bar.hide()
        self.status_bar_label = QLabel("", self)
        self.status_bar.addPermanentWidget(self.status_bar_label)
        self.setStatusBar(self.status_bar)
        self.setCentralWidget(self.tab_widget)

        # Create the initial tab
        self._new_tab(home_url)
        self._refresh_privacy_summary()

    def _get_current_tab(self) -> BrowserTab | None:
        """Get the currently active tab."""
        index = self.tab_widget.currentIndex()
        if index >= 0 and index in self.tabs:
            return self.tabs[index]
        return None

    def _on_navigate(self, target: str) -> None:
        """Handle navigation in the current tab."""
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        if target == "back":
            current_tab.web_view.back()
            return
        if target == "forward":
            current_tab.web_view.forward()
            return

        url_text = target
        if "://" not in url_text:
            url_text = "https://" + url_text
        current_tab.web_view.load(QUrl(url_text))

    def _reload_current_tab(self) -> None:
        """Reload the current tab."""
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.web_view.reload()

    def _home_current_tab(self) -> None:
        """Load home URL in the current tab."""
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.web_view.load(QUrl(self.home_url))

    def _close_current_tab(self) -> None:
        """Close the currently active tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self._close_tab(current_index)

    def _new_tab(self, url: str = "about:blank") -> None:
        """Create a new tab."""
        tab_index = self.tab_counter
        self.tab_counter += 1

        # Create web view with shared profile
        web_view = QWebEngineView(self)
        web_view.setPage(web_view.page())

        # Set up the page with shared profile
        from PySide6.QtWebEngineCore import QWebEnginePage
        page = QWebEnginePage(self.shared_profile, web_view)
        web_view.setPage(page)

        # Create tab wrapper
        tab = BrowserTab(web_view, self.default_container_name)
        self.tabs[tab_index] = tab

        # Connect signals for this tab
        web_view.urlChanged.connect(lambda url: self._on_url_changed(tab_index, url))
        web_view.loadFinished.connect(lambda ok: self._on_load_finished(tab_index, ok))
        web_view.titleChanged.connect(lambda title: self._on_title_changed(tab_index, title))

        # Install fingerprint protection for this tab
        self._install_fingerprint_protection_for_tab(tab_index)

        # Add to tab widget
        self.tab_widget.addTab(web_view, "New Tab")
        self.tab_widget.setCurrentIndex(tab_index)

        # Load the URL
        web_view.load(QUrl(url))
        LOGGER.info("new_tab_created", extra={"tab_index": tab_index, "url": url})

    def _close_tab(self, tab_index: int) -> None:
        """Close a tab and clean up all associated resources."""
        if tab_index not in self.tabs:
            return

        tab = self.tabs[tab_index]
        web_view = tab.web_view

        # Disconnect all signals connected to this web view
        web_view.disconnect()

        # Remove fingerprint protection scripts for this tab
        profile = self.shared_profile
        scripts = profile.scripts()
        script_name = f"ghostline-fingerprint-protection-{tab_index}"
        scripts_to_remove = [script for script in scripts.toList() if script.name() == script_name]
        for script in scripts_to_remove:
            scripts.remove(script)

        # Remove the tab widget
        self.tab_widget.removeTab(tab_index)

        # Remove from tracking
        del self.tabs[tab_index]

        LOGGER.info("tab_closed", extra={"tab_index": tab_index, "scripts_removed": len(scripts_to_remove)})

    def _on_tab_switched(self, tab_index: int) -> None:
        """Handle tab switch event."""
        current_tab = self._get_current_tab()
        if current_tab:
            # Update navigation bar with current tab's URL
            self._update_address_bar(current_tab.web_view.url())
            self._update_security_state(current_tab.web_view.url())
            LOGGER.info("tab_switched", extra={"tab_index": tab_index})

    def _on_url_changed(self, tab_index: int, url: QUrl) -> None:
        """Handle URL change in a tab."""
        if tab_index in self.tabs:
            tab = self.tabs[tab_index]
            # Only update UI if this is the active tab
            if self.tab_widget.currentIndex() == tab_index:
                self._update_address_bar(url)
                self._update_security_state(url)
                self._install_fingerprint_protection_for_tab(tab_index)

    def _on_title_changed(self, tab_index: int, title: str) -> None:
        """Handle title change in a tab."""
        if tab_index in self.tabs:
            self.tabs[tab_index].title = title
            # Update tab widget title
            self.tab_widget.setTabText(tab_index, title[:30] if title else "New Tab")

    def _on_load_finished(self, tab_index: int, ok: bool) -> None:
        """Handle load finished in a tab."""
        if tab_index == self.tab_widget.currentIndex():
            message = "Page loaded" if ok else "Failed to load page"
            LOGGER.info("navigation_status", extra={"success": ok, "status_message": message})
            self._refresh_privacy_summary()

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")

        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(lambda: self._new_tab())
        file_menu.addAction(new_tab_action)

        close_tab_action = QAction("Close Tab", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self._close_current_tab)
        file_menu.addAction(close_tab_action)

        new_session_action = QAction("New Session", self)
        new_session_action.setShortcut(QKeySequence.New)
        new_session_action.triggered.connect(lambda: self._new_tab("about:blank"))
        file_menu.addAction(new_session_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = menu.addMenu("&View")
        view_menu.addAction("Reload", self._reload_current_tab, QKeySequence.Refresh)
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
        self.dashboard.record_navigation(self.default_container_name, url.toString())

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

    def _install_fingerprint_protection_for_tab(self, tab_index: int) -> None:
        """Install JavaScript that enforces anti-fingerprinting protections for a specific tab."""
        if tab_index not in self.tabs:
            return

        tab = self.tabs[tab_index]
        profile = self.shared_profile
        scripts = profile.scripts()

        # Remove old fingerprint script if exists for this tab
        # (we use a unique name per tab)
        script_name = f"ghostline-fingerprint-protection-{tab_index}"
        for script in scripts.toList():
            if script.name() == script_name:
                scripts.remove(script)

        # Get or create fingerprint injector for this container
        container_name = tab.container_name
        if container_name not in self.fp_injectors:
            self.fp_injectors[container_name] = FingerprintInjector(self.dashboard, container_name)

        fp_injector = self.fp_injectors[container_name]

        # Generate script for current origin
        origin = self.dashboard._container_origins.get(container_name, "about:blank")
        script_source = fp_injector.generate_script(origin)

        # Create and configure script
        script = QWebEngineScript()
        script.setName(script_name)
        script.setSourceCode(script_source)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)

        # Only inject into actual web pages, not sandboxed pages like about:blank
        script.setRunsOnUrl(QUrl("*://*/*"))

        scripts.insert(script)
        LOGGER.info("fingerprint_protection_installed", extra={"origin": origin, "container": container_name, "tab_index": tab_index})

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.dashboard, self, container=self.default_container_name)
        if dialog.exec():
            container_badge = self.dashboard.container_ux.badge_for(self.default_container_name)
            if container_badge:
                self.navigation_bar.set_container_badge(
                    self.default_container_name,
                    container_badge.color,
                    container_badge.isolation_badge,
                )
            self._refresh_privacy_summary()

    def _refresh_privacy_summary(self) -> None:
        summary = self.dashboard.status_for_container(self.default_container_name)
        gating = self.dashboard.gating_snapshot(self.default_container_name)
        noise = self.dashboard.calibrated_noise_for(self.default_container_name)
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
