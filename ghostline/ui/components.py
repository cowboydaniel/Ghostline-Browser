"""Shared PySide6 UI components for the Ghostline shell."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ghostline.ui.dashboard import PrivacyDashboard


class NavigationBar(QToolBar):
    navigate_requested = Signal(str)
    reload_requested = Signal()
    home_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__("Navigation", parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(18, 18))
        self.setStyleSheet(
            "QToolBar { spacing: 8px; padding: 6px; border: 0px; background: #f7f7f7; }"
        )

        self.address_bar = QLineEdit(self)
        self.address_bar.setPlaceholderText("Search or enter address")
        self.address_bar.setClearButtonEnabled(True)
        self.address_bar.returnPressed.connect(self._handle_address_bar)

        back_action = QAction(self.style().standardIcon(QStyle.SP_ArrowBack), "Back", self)
        back_action.triggered.connect(lambda: self.navigate_requested.emit("back"))
        self.addAction(back_action)

        forward_action = QAction(
            self.style().standardIcon(QStyle.SP_ArrowForward), "Forward", self
        )
        forward_action.triggered.connect(lambda: self.navigate_requested.emit("forward"))
        self.addAction(forward_action)

        reload_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Reload", self)
        reload_action.triggered.connect(self.reload_requested.emit)
        self.addAction(reload_action)

        home_action = QAction(self.style().standardIcon(QStyle.SP_DesktopIcon), "Home", self)
        home_action.triggered.connect(self.home_requested.emit)
        self.addAction(home_action)

        settings_action = QAction(
            self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Settings", self
        )
        settings_action.triggered.connect(self.settings_requested.emit)
        self.addAction(settings_action)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        self.addWidget(self.address_bar)

        self.security_indicator = QLabel("🔒 Secure", self)
        self.security_indicator.setStyleSheet(
            "QLabel { padding: 4px 8px; border-radius: 6px; background: #e8f5e9; color: #256029; }"
        )
        self.addWidget(self.security_indicator)

    def _handle_address_bar(self) -> None:
        text = self.address_bar.text().strip()
        if text:
            self.navigate_requested.emit(text)

    def set_address(self, url: str) -> None:
        self.address_bar.setText(url)

    def update_security_state(self, secure: bool, host: Optional[str]) -> None:
        if secure:
            label = "🔒 Secure"
            style = "QLabel { padding: 4px 8px; border-radius: 6px; background: #e8f5e9; color: #256029; }"
        else:
            label = "⚠️ Not secure"
            style = "QLabel { padding: 4px 8px; border-radius: 6px; background: #fff3cd; color: #8a6d3b; }"
        if host:
            label = f"{label} — {host}"
        self.security_indicator.setText(label)
        self.security_indicator.setStyleSheet(style)


class SettingsDialog(QDialog):
    """Minimal settings surface that maps directly to privacy controls."""

    def __init__(self, dashboard: PrivacyDashboard, parent=None) -> None:
        super().__init__(parent)
        self.dashboard = dashboard
        self.setWindowTitle("Ghostline Settings")
        self.setMinimumWidth(360)

        self.connection_mode = QComboBox(self)
        self.connection_mode.addItems(["standard", "hardened", "laboratory"])

        self.ech_checkbox = QCheckBox("Enable Encrypted ClientHello (ECH)", self)
        self.https_only_checkbox = QCheckBox("Enforce HTTPS-Only mode", self)
        self.tor_checkbox = QCheckBox("Route through Tor where available", self)

        privacy_group = QGroupBox("Privacy and Security", self)
        privacy_layout = QVBoxLayout()
        privacy_layout.addWidget(self.ech_checkbox)
        privacy_layout.addWidget(self.https_only_checkbox)
        privacy_layout.addWidget(self.tor_checkbox)
        privacy_group.setLayout(privacy_layout)

        form_layout = QFormLayout()
        form_layout.addRow("Connection profile", self.connection_mode)
        form_layout.addRow(privacy_group)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel, parent=self
        )
        button_box.accepted.connect(self._apply_and_accept)
        button_box.rejected.connect(self.reject)

        root_layout = QVBoxLayout()
        root_layout.addLayout(form_layout)
        root_layout.addWidget(button_box)
        self.setLayout(root_layout)

        self._sync_from_dashboard()

    def _sync_from_dashboard(self) -> None:
        self.connection_mode.setCurrentText(self.dashboard.connection_mode)
        self.ech_checkbox.setChecked(self.dashboard.toggles.get("ech", False))
        self.https_only_checkbox.setChecked(self.dashboard.toggles.get("https_only", False))
        self.tor_checkbox.setChecked(self.dashboard.toggles.get("tor", False))

    def _apply_and_accept(self) -> None:
        self.dashboard.connection_mode = self.connection_mode.currentText()
        self.dashboard.toggle("ech", self.ech_checkbox.isChecked())
        self.dashboard.toggle("https_only", self.https_only_checkbox.isChecked())
        self.dashboard.toggle("tor", self.tor_checkbox.isChecked())
        self.accept()
