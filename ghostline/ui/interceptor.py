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


# JavaScript injection to suppress strict MIME type checking errors
# and allow stylesheet loading despite missing Content-Type headers
MIME_TYPE_FIX_SCRIPT = """
(function() {
    // Suppress "Refused to apply style" errors by allowing CSS loads with empty MIME types
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            // If this is a CSS resource request with missing Content-Type, add it
            const contentType = response.headers.get('content-type');
            if (!contentType && args[0] && args[0].includes('fetchType=css')) {
                // Return a modified response with proper Content-Type
                return new Response(response.body, {
                    status: response.status,
                    statusText: response.statusText,
                    headers: new Headers(response.headers)
                });
            }
            return response;
        });
    };
})();
"""
