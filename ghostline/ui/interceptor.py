"""QtWebEngine request interceptor to fix missing MIME types for stylesheets."""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor


class MimeTypeFixInterceptor(QWebEngineUrlRequestInterceptor):
    """Intercepts web requests and improves handling of stylesheet requests."""

    def interceptRequest(self, info):
        """Improve Accept headers for stylesheet requests."""
        url = info.requestUrl().toString()

        # For URLs that explicitly request CSS, ensure proper Accept header
        if "fetchType=css" in url or url.endswith(".css"):
            headers = info.requestHeaders()
            # Set proper Accept header to hint that we're requesting a stylesheet
            headers[b"Accept"] = b"text/css,*/*;q=0.1"
            info.setRequestHeaders(headers)
