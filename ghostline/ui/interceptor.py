"""QtWebEngine request interceptor to block problematic third-party endpoints."""
from __future__ import annotations

from pathlib import Path
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlSchemeHandler, QWebEngineUrlScheme
from PySide6.QtCore import QUrl, QByteArray, QBuffer, QIODevice


class MimeTypeFixInterceptor(QWebEngineUrlRequestInterceptor):
    """Intercepts web requests and blocks problematic third-party logging endpoints."""

    def interceptRequest(self, info):
        """Block Netflix logging endpoints that return invalid MIME types."""
        url = info.requestUrl().toString()

        # Block Netflix logging endpoints that cause MIME type validation errors
        # These are telemetry/logging only and not critical for page functionality
        if "logs.netflix.com" in url and "fetchType=css" in url:
            info.block(True)


class WelcomePageSchemeHandler(QWebEngineUrlSchemeHandler):
    """Handles ghostline: requests by serving HTML pages from the media directory."""

    def requestStarted(self, request):
        """Handle requests for ghostline: URLs."""
        url = request.requestUrl().toString()
        media_dir = Path(__file__).parent.parent / "media"

        # Map URLs to filenames
        url_map = {
            "ghostline:welcome": "welcome.html",
            "ghostline:privacy_dashboard": "privacy_dashboard.html",
            "ghostline:settings": "settings.html",
            "ghostline:shortcuts": "shortcuts.html",
        }

        filename = url_map.get(url)
        if filename:
            file_path = media_dir / filename
            if file_path.exists():
                content = file_path.read_bytes()
            else:
                # Fallback if file not found
                content = b"<html><body>Page not found</body></html>"

            # Use QBuffer to serve the content
            buffer = QBuffer(self)
            buffer.setData(QByteArray(content))
            buffer.open(QIODevice.ReadOnly)
            request.reply(b"text/html; charset=utf-8", buffer)
        else:
            # Unknown ghostline: URL
            content = b"<html><body>Unknown page</body></html>"
            buffer = QBuffer(self)
            buffer.setData(QByteArray(content))
            buffer.open(QIODevice.ReadOnly)
            request.reply(b"text/html; charset=utf-8", buffer)
