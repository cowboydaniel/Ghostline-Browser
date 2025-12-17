"""PySide6 application shell with QtWebEngine."""
from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar
from PySide6.QtWebEngineWidgets import QWebEngineView

from ghostline.logging_config import configure_logging, startup_banner
from .components import NavigationBar


class GhostlineWindow(QMainWindow):
    """Hardened browser shell with typed signals and status surfaces."""

    def __init__(self, home_url: str = "https://www.example.com") -> None:
        super().__init__()
        self.setWindowTitle("Ghostline Browser")
        self.resize(1280, 800)

        self.web_view = QWebEngineView(self)
        self.web_view.load(QUrl(home_url))
        self.web_view.urlChanged.connect(self._update_address_bar)
        self.web_view.loadFinished.connect(self._show_load_status)

        self.navigation_bar = NavigationBar(self)
        self.navigation_bar.navigate_requested.connect(self._on_navigate)
        self.navigation_bar.reload_requested.connect(self.web_view.reload)
        self.navigation_bar.home_requested.connect(lambda: self.web_view.load(QUrl(home_url)))
        self.addToolBar(self.navigation_bar)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.setCentralWidget(self.web_view)

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

    def _update_address_bar(self, url: QUrl) -> None:
        self.navigation_bar.set_address(url.toString())

    def _show_load_status(self, ok: bool) -> None:
        message = "Page loaded" if ok else "Failed to load page"
        logging.getLogger(__name__).info("navigation_status", extra={"success": ok})
        self.status_bar.showMessage(message, 2500)


def launch() -> None:
    configure_logging()
    startup_banner("ghostline")
    app = QApplication(sys.argv)
    window = GhostlineWindow()
    window.show()
    sys.exit(app.exec())
