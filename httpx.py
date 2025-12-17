"""Lightweight httpx-compatible shim for offline testing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class HTTPStatusError(Exception):
    pass


@dataclass
class Response:
    status_code: int
    text: str = ""
    headers: Dict[str, str] = field(default_factory=dict)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPStatusError(f"status={self.status_code}")

    def json(self) -> Any:
        """Return a JSON-decoded representation of ``text``.

        The real httpx.Response supports ``json()`` for convenience; replicating
        it here keeps the shim compatible with production code and tests that
        parse structured payloads.
        """

        import json

        return json.loads(self.text or "null")


class Client:
    def __init__(self, http2: bool = False, headers: Optional[Dict[str, str]] = None) -> None:
        self.http2 = http2
        self.headers = headers or {}

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        self.close()

    def close(self) -> None:
        return None

    def get(self, url: str) -> Response:
        return Response(200, text=f"client-placeholder:{url}", headers=self.headers)


class AsyncClient:
    def __init__(self, http2: bool = False, headers: Optional[Dict[str, str]] = None) -> None:
        self.http2 = http2
        self.headers = headers or {}

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        await self.aclose()

    async def aclose(self) -> None:
        return None

    async def get(self, url: str) -> Response:
        return Response(200, text=f"async-placeholder:{url}", headers=self.headers)


__all__ = ["Client", "AsyncClient", "Response", "HTTPStatusError"]
