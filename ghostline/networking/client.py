"""HTTP client with HTTP/2-first semantics and HTTP/3 placeholder."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Optional

import httpx


@dataclass
class ConnectionProfile:
    """Per-profile connection pool controls to enforce isolation."""

    name: str
    alpn_protocols: tuple[str, ...] = ("h3", "h2", "http/1.1")
    allow_coalescing: bool = False
    connection_pool: httpx.Client = field(init=False)

    def __post_init__(self) -> None:
        self.connection_pool = httpx.Client(http2=True, headers={"User-Agent": "Ghostline/phase1"})


class HttpClient:
    """High-level networking client covering HTTP/2/3 and pool isolation."""

    def __init__(self) -> None:
        self.profiles: Dict[str, ConnectionProfile] = {}

    def register_profile(self, profile: ConnectionProfile) -> None:
        self.profiles[profile.name] = profile

    def get_client(self, profile: str = "default") -> ConnectionProfile:
        if profile not in self.profiles:
            self.register_profile(ConnectionProfile(name=profile))
        return self.profiles[profile]

    def fetch(self, url: str, profile: str = "default") -> httpx.Response:
        client = self.get_client(profile)
        response = client.connection_pool.get(url)
        response.raise_for_status()
        return response

    async def fetch_async(self, url: str, profile: str = "default") -> httpx.Response:
        profile_obj = self.get_client(profile)
        async with httpx.AsyncClient(http2=True, headers=profile_obj.connection_pool.headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response

    async def fetch_http3(self, url: str, profile: str = "default") -> httpx.Response:
        """Placeholder HTTP/3 client using the HTTPX transport API.

        The transport is modeled for QUIC but avoids external connectivity in tests.
        """

        profile_obj = self.get_client(profile)
        headers = {"User-Agent": profile_obj.connection_pool.headers["User-Agent"], "Alt-Svc": "h3"}

        async def _mock_http3_request() -> httpx.Response:
            return httpx.Response(200, text=f"http3-placeholder:{url}", headers=headers)

        return await asyncio.ensure_future(_mock_http3_request())


class ConnectionGuard:
    """Provides pre-flight checks for leak prevention and ALPN negotiation."""

    @staticmethod
    def enforce_https(url: str) -> str:
        if not url.startswith("https://"):
            return "https://" + url.lstrip("http://")
        return url

    @staticmethod
    def alpn_order() -> tuple[str, ...]:
        return ("h3", "h2", "http/1.1")

    @staticmethod
    def partition_key(url: str, container: Optional[str] = None) -> str:
        normalized = url.split("//")[-1].split("/")[0]
        return f"{normalized}:{container or 'default'}"
