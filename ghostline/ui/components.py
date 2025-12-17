"""Shared PySide6 UI components for the Ghostline shell."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLineEdit, QToolBar


class NavigationBar(QToolBar):
    navigate_requested = Signal(str)
    reload_requested = Signal()
    home_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__("Navigation", parent)
        self.address_bar = QLineEdit(self)
        self.address_bar.returnPressed.connect(self._handle_address_bar)

        back_action = QAction("Back", self)
        back_action.triggered.connect(lambda: self.navigate_requested.emit("back"))
        self.addAction(back_action)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(lambda: self.navigate_requested.emit("forward"))
        self.addAction(forward_action)

        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.reload_requested.emit)
        self.addAction(reload_action)

        home_action = QAction("Home", self)
        home_action.triggered.connect(self.home_requested.emit)
        self.addAction(home_action)

        self.addWidget(self.address_bar)

    def _handle_address_bar(self) -> None:
        text = self.address_bar.text().strip()
        if text:
            self.navigate_requested.emit(text)

    def set_address(self, url: str) -> None:
        self.address_bar.setText(url)
