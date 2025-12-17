from ghostline.privacy.rfp import CanvasNoiseInjector, rounded_time, unified_user_agent
from ghostline.privacy.storage import PartitionedStore


def test_timer_rounding_is_bucketed():
    rounded = rounded_time(now=1700000000.123)
    assert rounded % 0.1 == 0


def test_canvas_noise_is_deterministic():
    injector = CanvasNoiseInjector(seed_secret="seed")
    noise_one = injector.noise_for_origin("https://example.com")
    noise_two = injector.noise_for_origin("https://example.com")
    assert noise_one == noise_two


def test_partitioned_store_isolation():
    store = PartitionedStore()
    store.set("example.com", "session", "abc", container="one")
    assert store.get("example.com", "session", container="two") is None


def test_unified_user_agent_freezes_platform():
    ua = unified_user_agent(platform="Test Platform")
    assert "Test Platform" in ua
