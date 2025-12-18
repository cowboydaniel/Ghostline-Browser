"""QtWebEngine request interceptor to block problematic third-party endpoints."""
from __future__ import annotations

from pathlib import Path
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlSchemeHandler
from PySide6.QtCore import QUrl, QByteArray


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
    """Handles ghostline:welcome requests by serving the welcome page HTML."""

    def requestStarted(self, request):
        """Handle requests for ghostline:welcome."""
        url = request.requestUrl().toString()

        if url == "ghostline:welcome":
            # Read the welcome.html file
            media_dir = Path(__file__).parent.parent / "media"
            welcome_file = media_dir / "welcome.html"

            if welcome_file.exists():
                content = welcome_file.read_bytes()
                request.reply(b"text/html; charset=utf-8", QByteArray(content))
            else:
                # Fallback if file not found
                fallback = b"<html><body>Welcome page not found</body></html>"
                request.reply(b"text/html; charset=utf-8", QByteArray(fallback))
