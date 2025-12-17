import sys
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QAction,
    QApplication,
    QLineEdit,
    QMainWindow,
    QStatusBar,
    QToolBar,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


class BrowserWindow(QMainWindow):
    """A minimal web browser window with navigation controls."""

    def __init__(self, home_url: str = "https://www.example.com") -> None:
        super().__init__()
        self.setWindowTitle("Ghostline Browser")
        self.resize(1024, 768)

        self.web_view = QWebEngineView(self)
        self.web_view.load(QUrl(home_url))
        self.web_view.urlChanged.connect(self.update_address_bar)
        self.web_view.loadFinished.connect(self.show_load_status)

        navigation_toolbar = self._build_toolbar()
        self.addToolBar(navigation_toolbar)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.setCentralWidget(self.web_view)

    def _build_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Navigation", self)

        back_action = QAction("Back", self)
        back_action.triggered.connect(self.web_view.back)
        toolbar.addAction(back_action)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(self.web_view.forward)
        toolbar.addAction(forward_action)

        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.web_view.reload)
        toolbar.addAction(reload_action)

        home_action = QAction("Home", self)
        home_action.triggered.connect(self.navigate_home)
        toolbar.addAction(home_action)

        self.address_bar = QLineEdit(self)
        self.address_bar.returnPressed.connect(self.load_from_address_bar)
        toolbar.addWidget(self.address_bar)

        return toolbar

    def navigate_home(self) -> None:
        self.web_view.load(QUrl("https://www.example.com"))

    def load_from_address_bar(self) -> None:
        url_text = self.address_bar.text().strip()
        if not url_text:
            return

        if "://" not in url_text:
            url_text = "https://" + url_text

        self.web_view.load(QUrl(url_text))

    def update_address_bar(self, url: QUrl) -> None:
        self.address_bar.setText(url.toString())

    def show_load_status(self, ok: bool) -> None:
        if ok:
            self.status_bar.showMessage("Page loaded", 2000)
        else:
            self.status_bar.showMessage("Failed to load page", 2000)


def main() -> None:
    app = QApplication(sys.argv)
    window = BrowserWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
