import asyncio
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: run test in event loop")


def pytest_pyfunc_call(pyfuncitem):
    asyncio_marker = pyfuncitem.get_closest_marker("asyncio")
    if asyncio_marker:
        loop = pyfuncitem._request.getfixturevalue("event_loop")
        loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
        return True


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
