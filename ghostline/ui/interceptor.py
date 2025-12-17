"""QtWebEngine request interceptor to block problematic third-party endpoints."""
from __future__ import annotations

from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor


class MimeTypeFixInterceptor(QWebEngineUrlRequestInterceptor):
    """Intercepts web requests and blocks problematic third-party logging endpoints."""

    def interceptRequest(self, info):
        """Block Netflix logging endpoints that return invalid MIME types."""
        url = info.requestUrl().toString()

        # Block Netflix logging endpoints that cause MIME type validation errors
        # These are telemetry/logging only and not critical for page functionality
        if "logs.netflix.com" in url and "fetchType=css" in url:
            info.block(True)
