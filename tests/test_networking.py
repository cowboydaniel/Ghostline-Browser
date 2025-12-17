import pytest

from ghostline.networking.client import ConnectionGuard, ConnectionProfile, HttpClient


class DummyTransport:
    def __init__(self):
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        return type("Resp", (), {"status_code": 200, "raise_for_status": lambda self: None})()


def test_alpn_order_matches_spec():
    assert ConnectionGuard.alpn_order() == ("h3", "h2", "http/1.1")


def test_connection_profiles_partition_by_name():
    client = HttpClient()
    profile = ConnectionProfile(name="container-a")
    dummy = DummyTransport()
    profile.connection_pool = dummy
    client.register_profile(profile)

    client.fetch("https://example.com", profile="container-a")
    assert dummy.calls == ["https://example.com"]


aSYNC_TIMEOUT = 5


@pytest.mark.asyncio
async def test_http3_placeholder_event_loop():
    client = HttpClient()
    response = await client.fetch_http3("https://example.com")
    assert response.text.startswith("http3-placeholder")
